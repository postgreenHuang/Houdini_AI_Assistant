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
        "Step 3 — EXECUTE: Generate ONE `run_python` script with MANDATORY two-phase structure:\n"
        "  Phase 1: Create ALL nodes and wire ALL connections FIRST.\n"
        "    !! EVERY node except the first MUST have a setInput() call.\n"
        "    !! For merge/switch nodes, specify input index: merge.setInput(0, A), merge.setInput(1, B).\n"
        "  Phase 2: Then set ALL parameters, each wrapped in try/except.\n"
        "  Report: Print the full connection chain and any parameter errors.\n"
    )
