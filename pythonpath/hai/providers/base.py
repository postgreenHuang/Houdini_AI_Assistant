"""Base interface for AI providers."""


class ProviderInterface:
    """All providers must implement this interface."""

    def __init__(self, api_key_or_url, model="", provider_name=""):
        self.api_key = api_key_or_url
        self.model = model
        self.provider_name = provider_name

    def send_message(self, messages, tools=None, system_prompt="", max_tokens=4096):
        """Send a message and return the response.

        Returns dict:
            {
                "content": str,              # text response
                "tool_calls": [              # list of tool calls (may be empty)
                    {
                        "id": str,
                        "name": str,
                        "arguments": dict,
                    },
                    ...
                ],
                "usage": {"input_tokens": int, "output_tokens": int},
            }
        """
        raise NotImplementedError

    def get_tool_schema(self, tool_name, description, parameters):
        """Convert a tool definition to this provider's native format."""
        raise NotImplementedError

    def count_tokens(self, text):
        """Estimate token count for text (rough approximation)."""
        # Rough estimate: ~4 chars per token for English, ~2 for Chinese
        return len(text) // 3
