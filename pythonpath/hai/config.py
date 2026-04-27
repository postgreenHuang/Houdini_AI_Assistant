"""Configuration management — API keys, provider selection, preferences."""

import json
import os

_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".houdini_ai_assistant")
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "provider": "claude",
    "api_keys": {
        "claude": "",
        "openai": "",
        "deepseek": "",
        "gemini": "",
        "glm": "",
        "ollama_url": "http://localhost:11434",
        "lmstudio_url": "http://localhost:1234",
    },
    "model": "",
    "allow_code_execution": False,
    "permission_level": "confirm",
    "max_context_nodes": 50,
    "system_prompt": "",
    "response_style": "normal",
    "language": "zh",
}


def _ensure_config_dir():
    if not os.path.exists(_CONFIG_DIR):
        os.makedirs(_CONFIG_DIR)


def load_config():
    """Load config from disk, falling back to defaults."""
    _ensure_config_dir()
    if os.path.exists(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            merged = dict(DEFAULT_CONFIG)
            merged.update(saved)
            return merged
        except (json.JSONDecodeError, IOError):
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg):
    """Persist config to disk."""
    _ensure_config_dir()
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def get_api_key(provider, cfg=None):
    """Return the API key for the given provider."""
    if cfg is None:
        cfg = load_config()
    keys = cfg.get("api_keys", {})
    return keys.get(provider, "")


def get_active_provider(cfg=None):
    """Return (provider_name, api_key_or_url, model) for the active provider."""
    if cfg is None:
        cfg = load_config()
    provider = cfg.get("provider", "claude")
    keys = cfg.get("api_keys", {})
    model = cfg.get("model", "")
    if provider == "ollama":
        return provider, keys.get("ollama_url", "http://localhost:11434"), model or "llama3"
    if provider == "lmstudio":
        return provider, keys.get("lmstudio_url", "http://localhost:1234"), model or "local-model"
    return provider, keys.get(provider, ""), model
