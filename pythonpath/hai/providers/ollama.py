"""Ollama / LM Studio provider — local models via OpenAI-compatible API."""

import json
import urllib.request
import urllib.error
from .base import ProviderInterface


class OllamaProvider(ProviderInterface):

    def __init__(self, base_url, model="", provider_name="ollama"):
        super().__init__(base_url, model, provider_name)
        self.base_url = base_url.rstrip("/")
        self.api_endpoint = "{}/v1/chat/completions".format(self.base_url)
        self.model = model or "llama3"

        # Ollama has no auth; LM Studio may or may not
        self.api_key = "no-key"

    def send_message(self, messages, tools=None, system_prompt="", max_tokens=4096):
        headers = {
            "Content-Type": "application/json",
        }

        formatted = self._format_messages(messages, system_prompt)

        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": formatted,
            "stream": False,
        }

        if tools:
            body["tools"] = [self._format_tool(t) for t in tools]

        req = urllib.request.Request(
            self.api_endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError("{} error ({}): {}".format(self.provider_name, e.code, error_body))
        except urllib.error.URLError as e:
            raise RuntimeError(
                "Cannot connect to {} at {}. Is it running?\nError: {}".format(
                    self.provider_name, self.base_url, e.reason
                )
            )

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
                text = "".join(b.get("text", "") for b in content if b.get("type") == "text")
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
