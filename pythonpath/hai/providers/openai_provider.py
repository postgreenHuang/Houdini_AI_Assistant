"""OpenAI-compatible provider — works with GPT, DeepSeek, Gemini, GLM (Zhipu AI)."""

import json
import urllib.request
import urllib.error
from .base import ProviderInterface


class OpenAIProvider(ProviderInterface):

    def __init__(self, api_key, model="", provider_name="openai", api_url=""):
        super().__init__(api_key, model, provider_name)
        self._custom_url = api_url
        self._setup_endpoints()

    def _setup_endpoints(self):
        if self.provider_name == "deepseek":
            self.api_base = "https://api.deepseek.com/v1/chat/completions"
            self.model = self.model or "deepseek-chat"
        elif self.provider_name == "gemini":
            self.api_base = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
            self.model = self.model or "gemini-2.0-flash"
        elif self.provider_name == "glm":
            self.api_base = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
            self.model = self.model or "glm-5.1"
        elif self.provider_name == "custom":
            url = self._custom_url.rstrip("/")
            if url.endswith("/chat/completions"):
                self.api_base = url
            else:
                self.api_base = url + "/chat/completions"
            self.model = self.model or "custom-model"
            if not self._custom_url:
                raise ValueError("Custom provider requires an API URL in settings.")
        else:
            self.api_base = "https://api.openai.com/v1/chat/completions"
            self.model = self.model or "gpt-4o"

    def send_message(self, messages, tools=None, system_prompt="", max_tokens=4096):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self.api_key),
        }

        # OpenRouter requires these extra headers
        if "openrouter.ai" in self.api_base:
            headers["HTTP-Referer"] = "https://github.com/postgreenHuang/Houdini_AI_Assistant"
            headers["X-Title"] = "Houdini AI Assistant"

        formatted = self._format_messages(messages, system_prompt)

        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": formatted,
        }

        if tools:
            body["tools"] = [self._format_tool(t) for t in tools]

        body_bytes = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self.api_base,
            data=body_bytes,
            headers=headers,
            method="POST",
        )

        raw = ""
        try:
            import ssl
            try:
                ctx = ssl.create_default_context()
                resp = urllib.request.urlopen(req, timeout=120, context=ctx)
            except ssl.SSLError:
                # Fallback: skip verification (some corporate envs / old Houdini)
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                resp = urllib.request.urlopen(req, timeout=120, context=ctx)

            raw = resp.read().decode("utf-8").strip()
            if not raw:
                raise RuntimeError(
                    "{} returned empty response (url: {})".format(
                        self.provider_name, self.api_base))
            data = json.loads(raw)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError("{} API error ({}): {}".format(self.provider_name, e.code, error_body))
        except json.JSONDecodeError as e:
            raise RuntimeError("{} returned non-JSON ({} chars): {} ... (url: {})".format(
                self.provider_name, len(raw), raw[:300], self.api_base))
        except Exception as e:
            raise RuntimeError("{} request failed: {} (url: {})".format(
                type(e).__name__, e, self.api_base))

        return self._parse_response(data)

    def _format_messages(self, messages, system_prompt=""):
        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "tool_result":
                formatted.append({
                    "role": "tool",
                    "tool_call_id": msg.get("tool_use_id", ""),
                    "content": content,
                })
            elif role == "assistant" and msg.get("tool_calls"):
                m = {
                    "role": "assistant",
                    "content": content if isinstance(content, str) else None,
                    "tool_calls": msg["tool_calls"],
                }
                if msg.get("reasoning_content"):
                    m["reasoning_content"] = msg["reasoning_content"]
                formatted.append(m)
            elif role == "assistant" and isinstance(content, list):
                # Anthropic-format content blocks, extract text
                text = "".join(b.get("text", "") for b in content if b.get("type") == "text")
                tool_calls = []
                for b in content:
                    if b.get("type") == "tool_use":
                        tool_calls.append({
                            "id": b["id"],
                            "type": "function",
                            "function": {
                                "name": b["name"],
                                "arguments": json.dumps(b.get("input", {})),
                            },
                        })
                if tool_calls:
                    formatted.append({
                        "role": "assistant",
                        "content": text or None,
                        "tool_calls": tool_calls,
                    })
                else:
                    m = {"role": "assistant", "content": text}
                    if msg.get("reasoning_content"):
                        m["reasoning_content"] = msg["reasoning_content"]
                    formatted.append(m)
            else:
                m = {"role": role, "content": content}
                if role == "assistant" and msg.get("reasoning_content"):
                    m["reasoning_content"] = msg["reasoning_content"]
                formatted.append(m)

        # Validate message sequence for API compliance
        return self._validate_sequence(formatted)

    @staticmethod
    def _validate_sequence(messages):
        """Ensure tool messages are paired correctly with tool_calls.

        Rules:
        1. Every tool message must follow an assistant with tool_calls
        2. Every tool_call_id in an assistant message must have a matching tool response
        3. Orphan tool messages (no preceding tool_calls) are removed
        4. Unanswered tool_calls have dummy tool responses added
        """
        cleaned = []
        for msg in messages:
            if msg.get("role") == "tool":
                # Check if we're inside a tool_calls block (last assistant had tool_calls)
                if cleaned and cleaned[-1].get("role") == "tool":
                    # Consecutive tool messages — check if any preceding assistant has tool_calls
                    has_tc = False
                    for prev in reversed(cleaned):
                        if prev.get("role") == "assistant" and "tool_calls" in prev:
                            has_tc = True
                            break
                        if prev.get("role") == "user" or prev.get("role") == "system":
                            break
                    if has_tc:
                        cleaned.append(msg)
                    # else: orphan tool, skip
                elif cleaned and cleaned[-1].get("role") == "assistant" and "tool_calls" in cleaned[-1]:
                    cleaned.append(msg)
                # else: orphan tool message, skip
            else:
                # Before adding a non-tool message, close any pending tool_calls
                if (msg.get("role") in ("user", "assistant", "system") and
                        cleaned and cleaned[-1].get("role") == "assistant" and
                        "tool_calls" in cleaned[-1]):
                    # Check which tool_call_ids are missing responses
                    expected_ids = {tc["id"] for tc in cleaned[-1].get("tool_calls", [])}
                    answered_ids = set()
                    for prev in reversed(cleaned):
                        if prev.get("role") == "tool":
                            answered_ids.add(prev.get("tool_call_id", ""))
                        else:
                            break
                    missing = expected_ids - answered_ids
                    for mid in missing:
                        cleaned.append({
                            "role": "tool",
                            "tool_call_id": mid,
                            "content": "Tool execution skipped.",
                        })
                cleaned.append(msg)

        # Final check: if last message is assistant with tool_calls, add dummy responses
        if cleaned and cleaned[-1].get("role") == "assistant" and "tool_calls" in cleaned[-1]:
            expected_ids = {tc["id"] for tc in cleaned[-1].get("tool_calls", [])}
            answered_ids = set()
            for prev in reversed(cleaned[:-1]):
                if prev.get("role") == "tool":
                    answered_ids.add(prev.get("tool_call_id", ""))
                else:
                    break
            for mid in expected_ids - answered_ids:
                cleaned.append({
                    "role": "tool",
                    "tool_call_id": mid,
                    "content": "Tool execution skipped.",
                })

        return cleaned

    def _format_tool(self, tool):
        return {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": {
                    "type": "object",
                    "properties": tool.get("parameters", {}),
                    "required": tool.get("required", []),
                },
            },
        }

    def _parse_response(self, data):
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content_text = message.get("content") or ""
        tool_calls = []

        for tc in message.get("tool_calls", []):
            func = tc.get("function", {})
            args = func.get("arguments", "{}")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append({
                "id": tc["id"],
                "name": func.get("name", ""),
                "arguments": args,
            })

        # Store raw assistant message for continuing conversation
        raw_assistant = dict(message)
        # Preserve reasoning_content for DeepSeek thinking mode
        reasoning = message.get("reasoning_content")
        if reasoning:
            raw_assistant["reasoning_content"] = reasoning
        if tool_calls:
            raw_assistant["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["arguments"]),
                    },
                }
                for tc in tool_calls
            ]

        return {
            "content": content_text,
            "tool_calls": tool_calls,
            "usage": {
                "input_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                "output_tokens": data.get("usage", {}).get("completion_tokens", 0),
            },
            "raw_assistant": raw_assistant,
        }

    def get_tool_schema(self, tool_name, description, parameters):
        return self._format_tool({
            "name": tool_name,
            "description": description,
            "parameters": parameters,
        })
