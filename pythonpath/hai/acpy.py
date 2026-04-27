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
        "The user has activated Action Mode. They want you to actually BUILD things, "
        "not just explain. Use tools to create nodes, set parameters, connect them, "
        "and build the complete setup described in the prompt.\n\n"
        "Guidelines:\n"
        "- Create all necessary nodes step by step\n"
        "- Connect them in the correct order\n"
        "- Set all relevant parameters\n"
        "- Add Null nodes at the end for clean output\n"
        "- Report what you created when done\n"
    )
