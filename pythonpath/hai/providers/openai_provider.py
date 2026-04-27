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
            self.api_base = self._custom_url
            self.model = self.model or "custom-model"
            if not self.api_base:
                raise ValueError("Custom provider requires an API URL in settings.")
        else:
            self.api_base = "https://api.openai.com/v1/chat/completions"
            self.model = self.model or "gpt-4o"

    def send_message(self, messages, tools=None, system_prompt="", max_tokens=4096):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self.api_key),
        }

        formatted = self._format_messages(messages, system_prompt)

        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": formatted,
        }

        if tools:
            body["tools"] = [self._format_tool(t) for t in tools]

        req = urllib.request.Request(
            self.api_base,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError("{} API error ({}): {}".format(self.provider_name, e.code, error_body))
        except urllib.error.URLError as e:
            raise RuntimeError("Network error: {}".format(e.reason))

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
                formatted.append({
                    "role": "assistant",
                    "content": content if isinstance(content, str) else None,
                    "tool_calls": msg["tool_calls"],
                })
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
                    formatted.append({"role": "assistant", "content": text})
            else:
                formatted.append({"role": role, "content": content})

        return formatted

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
