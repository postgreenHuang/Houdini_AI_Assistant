"""ACPY Action Mode — prefix-triggered execution of scene operations."""


def is_acpy_prompt(text):
    """Check if a prompt starts with the ACPY action prefix."""
    return text.strip().upper().startswith("ACPY:")


def strip_acpy_prefix(text):
    """Remove the ACPY: prefix from a prompt."""
    stripped = text.strip()
    if stripped.upper().startswith("ACPY:"):
        return stripped[5:].strip()
    return stripped


def build_acpy_system_addition():
    """Return the extra system prompt text for ACPY mode."""
    return (
        "\n## ACPY Action Mode Active\n"
        "The user wants you to BUILD something. Follow the 3-step workflow:\n\n"
        "Step 1 — THINK: Analyze the request. List the nodes needed, their connection order, "
        "and key parameters. Show a simple chain diagram like: grid -> mountain -> null.\n\n"
        "Step 2 — INSPECT: Use get_selected_nodes, get_scene_info, or list_nodes to "
        "understand the current scene. Where should new nodes go? What existing nodes to connect to?\n\n"
        "Step 3 — EXECUTE: Generate ONE `run_python` script that creates everything. "
        "Use Python variables for node references. Wire with setInput. Set parameters. "
        "Add Null at end. Include print() for the report.\n"
    )
