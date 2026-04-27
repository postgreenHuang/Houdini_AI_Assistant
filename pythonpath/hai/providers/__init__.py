"""AI Provider abstraction layer."""

from .base import ProviderInterface
from .claude import ClaudeProvider
from .openai_provider import OpenAIProvider
from .ollama import OllamaProvider

PROVIDERS = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "deepseek": OpenAIProvider,
    "gemini": OpenAIProvider,
    "glm": OpenAIProvider,
    "ollama": OllamaProvider,
    "lmstudio": OllamaProvider,
}


def get_provider(name, api_key_or_url, model=""):
    """Factory: return a configured provider instance."""
    cls = PROVIDERS.get(name)
    if cls is None:
        raise ValueError("Unknown provider: {}. Available: {}".format(name, list(PROVIDERS.keys())))
    return cls(api_key_or_url, model=model, provider_name=name)
