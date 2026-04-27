"""Roles system — different AI personas with tailored System Prompts."""

import os

_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "..", "prompts")

ROLES = {
    "analyst": {
        "name": "Scene Analyst",
        "description": "Analyze scene structure, explain data flow, suggest improvements.",
        "system_prompt_suffix": (
            "\nYou are in Scene Analyst mode. Focus on analyzing the scene structure, "
            "explaining data flow between nodes, and suggesting improvements. "
            "Use get_selected_nodes and get_node_info to understand the network."
        ),
    },
    "debugger": {
        "name": "Debugger",
        "description": "Diagnose errors, find root causes, suggest fixes.",
        "system_prompt_suffix": (
            "\nYou are in Debugger mode. Focus on finding errors and their root causes. "
            "Check node warnings, errors, and upstream connections. "
            "Use get_node_info and get_node_tree to trace issues."
        ),
    },
    "coder": {
        "name": "Code Generator",
        "description": "Generate VEX and Python code with Houdini context.",
        "system_prompt_suffix": (
            "\nYou are in Code Generator mode. Focus on generating VEX wrangles and "
            "Python scripts for Houdini. Provide complete, runnable code. "
            "Suggest performance optimizations when relevant."
        ),
    },
    "documenter": {
        "name": "Technical Documenter",
        "description": "Generate technical documentation for nodes and networks.",
        "system_prompt_suffix": (
            "\nYou are in Technical Documenter mode. Generate clear technical documentation "
            "for the selected nodes: I/O description, key parameters, attributes, pitfalls. "
            "Format output in Markdown."
        ),
    },
    "assistant": {
        "name": "General Assistant",
        "description": "General-purpose Houdini AI assistant. Can do everything.",
        "system_prompt_suffix": "",
    },
}


def get_role(role_id):
    """Return role dict or default to 'assistant'."""
    return ROLES.get(role_id, ROLES["assistant"])


def get_role_names():
    """Return list of (id, display_name) tuples."""
    return [(k, v["name"]) for k, v in ROLES.items()]


def build_system_prompt(base_prompt="", role_id="assistant", context=""):
    """Build the full system prompt by combining base, role, and context."""
    parts = []

    if base_prompt:
        parts.append(base_prompt)
    else:
        parts.append(_default_base_prompt())

    role = get_role(role_id)
    if role["system_prompt_suffix"]:
        parts.append(role["system_prompt_suffix"])

    if context:
        parts.append("\n## Current Scene Context\n\n" + context)

    return "\n".join(parts)


def _default_base_prompt():
    return (
        "You are an AI assistant embedded inside SideFX Houdini. "
        "You help users work with their Houdini scenes.\n\n"
        "## Capabilities\n"
        "- Query scene state (selected nodes, parameters, connections)\n"
        "- Create, delete, connect, rename, copy nodes\n"
        "- Read and modify node parameters\n"
        "- Set expressions and keyframes\n"
        "- Analyze node networks and debug issues\n"
        "- Generate VEX and Python code\n\n"
        "## Rules\n"
        "- Always use tools to inspect the scene before answering about it.\n"
        "- When the user asks you to modify the scene, use the appropriate tools.\n"
        "- For write operations, describe what you're about to do before doing it.\n"
        "- If a tool returns an error, explain it to the user and suggest alternatives.\n"
        "- Respond in the same language the user uses.\n"
    )
