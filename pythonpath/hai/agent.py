"""Agent core — message loop, tool dispatch, conversation management."""

from .providers import get_provider
from .tools import get_ai_tools, execute_tool
from .roles import build_system_prompt
from .context import build_selection_context, build_scene_context
from .acpy import is_acpy_prompt, strip_acpy_prefix, build_acpy_system_addition
from .permissions import confirm_batch_operations, auto_save_hip, has_write_operations
from .config import load_config, get_active_provider

# Max auto-retries for run_python errors before giving up
_MAX_AUTO_RETRIES = 2


class Agent:
    """State-machine agent: alternates between background HTTP and main-thread tools."""

    def __init__(self, on_response=None, on_tool_call=None, on_error=None,
                 on_token_update=None, on_request_done=None):
        self.on_response = on_response or (lambda t: None)
        self.on_tool_call = on_tool_call or (lambda n, a: None)
        self.on_error = on_error or (lambda e: None)
        self.on_token_update = on_token_update or (lambda i, o: None)
        self.on_request_done = on_request_done or (lambda: None)

        self.messages = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.provider = None
        self.system_prompt = ""
        self.role = "assistant"
        self.context_text = ""
        self.max_tool_rounds = 10

        # State for the conversation loop
        self._sys_prompt = ""
        self._write_confirmed = False
        self._tools = []
        self._active = False
        self._retry_count = 0

    def reset(self):
        self.messages = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def get_messages(self):
        return list(self.messages)

    def set_messages(self, messages):
        self.messages = list(messages)

    def get_token_usage(self):
        return {"input": self.total_input_tokens, "output": self.total_output_tokens}

    def setup_provider(self, cfg=None):
        if cfg is None:
            cfg = load_config()
        provider_name, api_key, model, url = get_active_provider(cfg)
        if not api_key:
            raise ValueError(
                "No API key configured for provider '{}'. "
                "Please set it in Settings.".format(provider_name)
            )
        self.provider = get_provider(provider_name, api_key, model, url)
        self.system_prompt = cfg.get("system_prompt", "")

    def set_context(self, context_text):
        self.context_text = context_text

    def analyze_selection(self):
        self.context_text = build_selection_context()
        return self.context_text

    def analyze_scene(self):
        self.context_text = build_scene_context()
        return self.context_text

    # ---- State machine ----

    def start_conversation(self, user_text):
        if self.provider is None:
            self.setup_provider()

        acpy_active = is_acpy_prompt(user_text)
        if acpy_active:
            user_text = strip_acpy_prefix(user_text)

        self._sys_prompt = build_system_prompt(
            base_prompt=self.system_prompt,
            role_id=self.role,
            context=self.context_text,
        )
        if acpy_active:
            self._sys_prompt += build_acpy_system_addition()

        self.messages.append({"role": "user", "content": user_text})
        self._tools = get_ai_tools()
        self._write_confirmed = False
        self._active = True
        self._retry_count = 0

        self._start_http_round()

    def _start_http_round(self):
        import threading

        messages = list(self.messages)
        tools = self._tools
        sys_prompt = self._sys_prompt
        provider = self.provider

        def http_request():
            try:
                response = provider.send_message(
                    messages=messages,
                    tools=tools if tools else None,
                    system_prompt=sys_prompt,
                )
                self._on_http_response(response)
            except Exception as e:
                self.on_error("AI Provider Error: {}".format(str(e)))
                self._active = False
                self.on_request_done()

        threading.Thread(target=http_request, daemon=True).start()

    def _on_http_response(self, response):
        usage = response.get("usage", {})
        self.total_input_tokens += usage.get("input_tokens", 0)
        self.total_output_tokens += usage.get("output_tokens", 0)
        self.on_token_update(self.total_input_tokens, self.total_output_tokens)

        text = response.get("content", "")
        tool_calls = response.get("tool_calls", [])

        if text:
            self.on_response(text)

        if not tool_calls:
            if "raw_assistant" in response:
                self.messages.append({
                    "role": "assistant",
                    "content": text,
                    "tool_calls": response["raw_assistant"].get("tool_calls"),
                })
            else:
                self.messages.append({"role": "assistant", "content": text})
            self._active = False
            self.on_request_done()
            return

        if "raw_assistant" in response:
            self.messages.append({
                "role": "assistant",
                "content": text,
                "tool_calls": response["raw_assistant"].get("tool_calls"),
            })
        else:
            self.messages.append({"role": "assistant", "content": text})

        self._pending_ops = []
        for tc in tool_calls:
            self._pending_ops.append((tc["name"], tc["id"], tc["arguments"]))
            self.on_tool_call(tc["name"], tc["arguments"])

        self.on_request_done()

    def execute_pending_tools(self):
        """Main thread: execute tools, auto-retry on run_python errors."""
        if not self._active or not hasattr(self, '_pending_ops'):
            return

        ops = self._pending_ops
        del self._pending_ops

        # Confirm write operations
        has_writes = has_write_operations(
            [{"name": n, "arguments": a} for n, _, a in ops]
        )
        if has_writes and not self._write_confirmed:
            auto_save_hip()
            summaries = [
                ("{}".format(name), "{}({})".format(name, _short_args(args)))
                for name, _, args in ops
            ]
            if not confirm_batch_operations(summaries):
                for _, tool_id, _ in ops:
                    self.messages.append({
                        "role": "tool_result",
                        "content": "User denied this operation.",
                        "tool_use_id": tool_id,
                    })
                self._start_http_round()
                return
            self._write_confirmed = True

        # Execute tools
        had_error = False
        for tool_name, tool_id, tool_args in ops:
            success, result = execute_tool(tool_name, tool_args)
            if not success:
                self.on_error(result)
                had_error = True

            # Feature 4: Auto-retry — inject scene state on run_python errors
            if tool_name == "run_python" and not success:
                self._retry_count += 1
                if self._retry_count <= _MAX_AUTO_RETRIES:
                    scene_hint = self._get_error_context_hint()
                    result += (
                        "\n\n[SYSTEM] This error occurred during execution (attempt {}/{}). "
                        "Current scene state:\n{}".format(
                            self._retry_count, _MAX_AUTO_RETRIES, scene_hint)
                    )

            self.messages.append({
                "role": "tool_result",
                "content": result,
                "tool_use_id": tool_id,
            })

        if self._active:
            self._start_http_round()

    def _get_error_context_hint(self):
        """Get a brief snapshot of current scene for error recovery."""
        try:
            import hou
            parts = []
            obj = hou.node("/obj")
            if obj:
                for child in obj.children()[:10]:
                    parts.append(child.path() + " [" + child.type().name() + "]")
                    for sub in child.children()[:20]:
                        inputs = sub.inputs()
                        inp_str = ""
                        if inputs:
                            inp_str = " <- " + ", ".join(
                                i.name() for i in inputs if i
                            )
                        parts.append("  {} ({}){}".format(
                            sub.name(), sub.type().name(), inp_str))
            return "\n".join(parts) if parts else "Empty scene"
        except Exception:
            return "Unable to read scene state"


def _short_args(args, max_len=80):
    import json
    s = json.dumps(args, default=str)
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s
