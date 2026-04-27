"""Agent core — message loop, tool dispatch, conversation management."""

from .providers import get_provider
from .tools import get_ai_tools, execute_tool
from .roles import build_system_prompt
from .context import build_selection_context, build_scene_context
from .acpy import is_acpy_prompt, strip_acpy_prefix, build_acpy_system_addition
from .permissions import confirm_batch_operations, auto_save_hip, has_write_operations
from .config import load_config, get_active_provider


class Agent:
    """Manages conversation with AI, tool execution, and context."""

    def __init__(self, on_response=None, on_tool_call=None, on_error=None, on_token_update=None):
        self.on_response = on_response or (lambda t: None)
        self.on_tool_call = on_tool_call or (lambda n, a: None)
        self.on_error = on_error or (lambda e: None)
        self.on_token_update = on_token_update or (lambda i, o: None)

        self.messages = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.provider = None
        self.system_prompt = ""
        self.role = "assistant"
        self.context_text = ""
        self.max_tool_rounds = 10

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

    def _run_tool_on_main_thread(self, tool_name, tool_args):
        """Execute a single tool on the main thread via hou.ui API."""
        import hou

        def _do():
            return execute_tool(tool_name, tool_args)

        try:
            return hou.ui.executeInMainThreadWithResult(_do)
        except Exception:
            # Fallback: try direct execution (might be already on main thread)
            return execute_tool(tool_name, tool_args)

    def send_message(self, user_text):
        """Send a user message and process the full response loop.

        Designed to run on a background thread. HTTP requests here,
        tool execution delegated to main thread via hou.ui API.
        """
        if self.provider is None:
            self.setup_provider()

        acpy_active = is_acpy_prompt(user_text)
        if acpy_active:
            user_text = strip_acpy_prefix(user_text)

        sys_prompt = build_system_prompt(
            base_prompt=self.system_prompt,
            role_id=self.role,
            context=self.context_text,
        )
        if acpy_active:
            sys_prompt += build_acpy_system_addition()

        self.messages.append({"role": "user", "content": user_text})

        tools = get_ai_tools()
        final_text = ""
        cfg = load_config()
        write_confirmed = False

        for round_num in range(self.max_tool_rounds):
            try:
                response = self.provider.send_message(
                    messages=self.messages,
                    tools=tools if tools else None,
                    system_prompt=sys_prompt,
                )
            except Exception as e:
                error_msg = "AI Provider Error: {}".format(str(e))
                self.on_error(error_msg)
                if self.messages and self.messages[-1]["role"] == "user":
                    self.messages.pop()
                return error_msg

            usage = response.get("usage", {})
            self.total_input_tokens += usage.get("input_tokens", 0)
            self.total_output_tokens += usage.get("output_tokens", 0)
            self.on_token_update(self.total_input_tokens, self.total_output_tokens)

            text = response.get("content", "")
            tool_calls = response.get("tool_calls", [])

            if text:
                final_text = text
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
                break

            if "raw_assistant" in response:
                self.messages.append({
                    "role": "assistant",
                    "content": text,
                    "tool_calls": response["raw_assistant"].get("tool_calls"),
                })
            else:
                self.messages.append({"role": "assistant", "content": text})

            ops = []
            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc["arguments"]
                desc = "{}({})".format(tool_name, _short_args(tool_args))
                ops.append((tool_name, desc, tc["id"], tool_args))
                self.on_tool_call(tool_name, tool_args)

            has_writes = has_write_operations(tool_calls)
            if has_writes and not write_confirmed:
                auto_save_hip()
                summaries = [(op[0], op[1]) for op in ops]
                if not confirm_batch_operations(summaries):
                    for op in ops:
                        self.messages.append({
                            "role": "tool_result",
                            "content": "User denied this operation.",
                            "tool_use_id": op[2],
                        })
                    continue
                write_confirmed = True

            # Execute tools on main thread via hou.ui API
            for tool_name, desc, tool_id, tool_args in ops:
                success, result = self._run_tool_on_main_thread(tool_name, tool_args)
                if not success:
                    self.on_error(result)

                self.messages.append({
                    "role": "tool_result",
                    "content": result,
                    "tool_use_id": tool_id,
                })

        return final_text


def _short_args(args, max_len=80):
    import json
    s = json.dumps(args, default=str)
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s
