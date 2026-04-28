"""Configuration management — API keys, provider selection, preferences."""

import json
import os

_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".houdini_ai_assistant")
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "provider": "claude",
    "providers": {
        "claude": {
            "api_key": "",
            "url": "https://api.anthropic.com",
            "model": "claude-sonnet-4-6-20250514",
        },
        "openai": {
            "api_key": "",
            "url": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-4o",
        },
        "deepseek": {
            "api_key": "",
            "url": "https://api.deepseek.com/v1/chat/completions",
            "model": "deepseek-chat",
        },
        "gemini": {
            "api_key": "",
            "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            "model": "gemini-2.0-flash",
        },
        "glm": {
            "api_key": "",
            "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            "model": "glm-5.1",
        },
        "ollama": {
            "api_key": "",
            "url": "http://localhost:11434/v1/chat/completions",
            "model": "llama3",
        },
        "lmstudio": {
            "api_key": "",
            "url": "http://localhost:1234/v1/chat/completions",
            "model": "local-model",
        },
        "custom": {
            "api_key": "",
            "url": "",
            "model": "",
        },
    },
    "allow_code_execution": False,
    "permission_level": "confirm",
    "max_context_nodes": 50,
    "max_message_rounds": 20,
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
            # Deep merge providers dict
            if "providers" in saved:
                merged["providers"] = dict(DEFAULT_CONFIG["providers"])
                for k, v in saved["providers"].items():
                    if isinstance(v, dict) and k in merged["providers"]:
                        merged["providers"][k] = dict(merged["providers"][k])
                        merged["providers"][k].update(v)
                    else:
                        merged["providers"][k] = v
                saved.pop("providers")
            # Top-level overrides
            merged.update(saved)
            # Remove old flat format
            merged.pop("api_keys", None)
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
    return cfg.get("providers", {}).get(provider, {}).get("api_key", "")


def get_active_provider(cfg=None):
    """Return (provider_name, api_key, model, url) for the active provider."""
    if cfg is None:
        cfg = load_config()
    provider = cfg.get("provider", "claude")
    p = cfg.get("providers", {}).get(provider, {})
    api_key = p.get("api_key", "")
    model = p.get("model", "")
    url = p.get("url", "")
    return provider, api_key, model, url
