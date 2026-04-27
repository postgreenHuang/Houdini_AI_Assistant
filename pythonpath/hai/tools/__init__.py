"""Tool registry — central place to register and look up AI-callable tools."""

_TOOLS = {}


def register_tool(name, description, parameters, required, execute_fn):
    """Register a tool that the AI can call.

    Args:
        name: Tool name (e.g. "create_node")
        description: What the tool does (shown to AI)
        parameters: JSON Schema properties dict
        required: List of required parameter names
        execute_fn: Callable(**kwargs) -> str (returns result description)
    """
    _TOOLS[name] = {
        "name": name,
        "description": description,
        "parameters": parameters,
        "required": required,
        "execute": execute_fn,
    }


def get_tool(name):
    """Return tool definition dict or None."""
    return _TOOLS.get(name)


def get_all_tools():
    """Return list of all registered tool definitions (for AI provider)."""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["parameters"],
            "required": t["required"],
        }
        for t in _TOOLS.values()
    ]


def execute_tool(name, arguments):
    """Execute a tool by name with the given arguments.

    Returns (success: bool, result: str)
    """
    tool = _TOOLS.get(name)
    if tool is None:
        return False, "Unknown tool: {}".format(name)
    try:
        result = tool["execute"](**arguments)
        return True, result
    except Exception as e:
        return False, "Error executing {}: {}".format(name, str(e))


def tool_names():
    """Return all registered tool names."""
    return list(_TOOLS.keys())


# Auto-import tool modules to trigger registration
from . import node_ops  # noqa: E402, F401
from . import param_ops  # noqa: E402, F401
from . import scene_query  # noqa: E402, F401
