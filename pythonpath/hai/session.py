"""Session management — save, load, list, export conversation sessions."""

import json
import os
import uuid
from datetime import datetime

_SESSIONS_DIR = os.path.join(os.path.expanduser("~"), ".houdini_ai_assistant", "sessions")


def _ensure_dir():
    if not os.path.exists(_SESSIONS_DIR):
        os.makedirs(_SESSIONS_DIR)


def _session_filepath(session_id):
    return os.path.join(_SESSIONS_DIR, session_id + ".json")


def create_session():
    """Create a new empty session. Returns session_id."""
    _ensure_dir()
    session_id = uuid.uuid4().hex[:12]
    now = datetime.now().isoformat(timespec="seconds")
    data = {
        "id": session_id,
        "title": "",
        "created_at": now,
        "updated_at": now,
        "messages": [],
        "token_usage": {"input": 0, "output": 0},
    }
    with open(_session_filepath(session_id), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return session_id


def list_sessions():
    """Return all session summaries sorted by updated_at (newest first)."""
    _ensure_dir()
    sessions = []
    for fname in os.listdir(_SESSIONS_DIR):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(_SESSIONS_DIR, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
            sessions.append({
                "id": data.get("id", fname[:-5]),
                "title": data.get("title", "(untitled)"),
                "updated_at": data.get("updated_at", ""),
            })
        except (json.JSONDecodeError, IOError):
            continue
    sessions.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
    return sessions


def load_session(session_id):
    """Load full session data by id."""
    path = _session_filepath(session_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_session(session_id, messages, token_usage=None, title=None):
    """Save or update a session."""
    _ensure_dir()
    path = _session_filepath(session_id)
    now = datetime.now().isoformat(timespec="seconds")

    # Load existing to preserve created_at
    existing = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # Auto-title from first user message
    if not title and not existing.get("title"):
        for msg in messages:
            if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                title = msg["content"][:40].replace("\n", " ")
                break

    data = {
        "id": session_id,
        "title": title or existing.get("title", ""),
        "created_at": existing.get("created_at", now),
        "updated_at": now,
        "messages": _serialize_messages(messages),
        "token_usage": token_usage or existing.get("token_usage", {"input": 0, "output": 0}),
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def delete_session(session_id):
    """Delete a session file."""
    path = _session_filepath(session_id)
    if os.path.exists(path):
        os.remove(path)


def export_session(session_id, filepath):
    """Export session to an external JSON file."""
    data = load_session(session_id)
    if data is None:
        raise FileNotFoundError("Session '{}' not found.".format(session_id))
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def import_session(filepath):
    """Import a session from a JSON file. Returns new session_id."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    new_id = create_session()
    save_session(
        new_id,
        data.get("messages", []),
        token_usage=data.get("token_usage"),
        title=data.get("title", "(imported)"),
    )
    return new_id


def _serialize_messages(messages):
    """Strip non-serializable fields from messages before saving."""
    cleaned = []
    for msg in messages:
        m = {"role": msg["role"]}
        content = msg.get("content")
        if isinstance(content, str):
            m["content"] = content
        elif isinstance(content, list):
            # Anthropic-format content blocks — extract text only
            text = ""
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text += block.get("text", "")
            m["content"] = text
        else:
            m["content"] = str(content)

        if "tool_use_id" in msg:
            m["tool_use_id"] = msg["tool_use_id"]

        cleaned.append(m)
    return cleaned
