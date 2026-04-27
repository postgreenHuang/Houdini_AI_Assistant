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
    "custom": OpenAIProvider,
}


def get_provider(name, api_key, model="", url=""):
    """Factory: return a configured provider instance."""
    cls = PROVIDERS.get(name)
    if cls is None:
        raise ValueError("Unknown provider: {}. Available: {}".format(name, list(PROVIDERS.keys())))
    if name == "custom":
        if not url:
            raise ValueError("Custom provider requires an API URL.")
        return cls(api_key, model=model, provider_name=name, api_url=url)
    if name in ("ollama", "lmstudio"):
        # Ollama uses url as first arg (base_url), key is unused
        return cls(url or "http://localhost:11434", model=model, provider_name=name)
    return cls(api_key, model=model, provider_name=name)
