"""Anthropic Claude provider — Tool Use via Messages API."""

import json
import urllib.request
import urllib.error
from .base import ProviderInterface

API_BASE = "https://api.anthropic.com/v1/messages"


class ClaudeProvider(ProviderInterface):

    def __init__(self, api_key, model="", provider_name="claude"):
        super().__init__(api_key, model, provider_name)
        self.model = model or "claude-sonnet-4-6-20250514"

    def send_message(self, messages, tools=None, system_prompt="", max_tokens=4096):
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": self._format_messages(messages),
        }

        if system_prompt:
            body["system"] = system_prompt

        if tools:
            body["tools"] = [self._format_tool(t) for t in tools]

        req = urllib.request.Request(
            API_BASE,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError("Claude API error ({}): {}".format(e.code, error_body))
        except urllib.error.URLError as e:
            raise RuntimeError("Network error: {}".format(e.reason))

        return self._parse_response(data)

    def _format_messages(self, messages):
        """Convert our message format to Anthropic's format."""
        formatted = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "tool_result":
                formatted.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.get("tool_use_id", ""),
                        "content": content,
                    }],
                })
            elif role == "assistant" and isinstance(content, list):
                # Assistant message with tool_use blocks
                formatted.append({"role": "assistant", "content": content})
            else:
                formatted.append({"role": role, "content": content})

        return formatted

    def _format_tool(self, tool):
        """Convert our tool format to Anthropic's tool schema."""
        return {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": {
                "type": "object",
                "properties": tool.get("parameters", {}),
                "required": tool.get("required", []),
            },
        }

    def _parse_response(self, data):
        """Parse Anthropic API response into our unified format."""
        content_text = ""
        tool_calls = []

        for block in data.get("content", []):
            if block["type"] == "text":
                content_text += block["text"]
            elif block["type"] == "tool_use":
                tool_calls.append({
                    "id": block["id"],
                    "name": block["name"],
                    "arguments": block.get("input", {}),
                })

        # Store assistant content blocks for continuing conversation
        assistant_content = data.get("content", [])

        return {
            "content": content_text,
            "tool_calls": tool_calls,
            "usage": {
                "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                "output_tokens": data.get("usage", {}).get("output_tokens", 0),
            },
            "raw_content": assistant_content,
        }

    def get_tool_schema(self, tool_name, description, parameters):
        return self._format_tool({
            "name": tool_name,
            "description": description,
            "parameters": parameters,
        })
