"""Parameter read/write operations."""

import hou
from . import register_tool


# --- set_parameter ---

def _set_parameter(node_path, parm_name, value):
    try:
        node = hou.node(node_path)
        if node is None:
            return "Error: Node '{}' not found.".format(node_path)

        parm = node.parm(parm_name)
        if parm is None:
            # Try tuple-style parm (e.g. "t" for "tx", "ty", "tz")
            parm_tuple = node.parmTuple(parm_name)
            if parm_tuple is not None:
                if isinstance(value, list):
                    parm_tuple.set(value)
                    return "Set {}:{} = {}".format(node_path, parm_name, value)
                else:
                    return "Error: Parm '{}' is a tuple, provide a list of values.".format(parm_name)
            return "Error: Parameter '{}' not found on '{}'.".format(parm_name, node_path)

        # Handle different value types
        if isinstance(value, list):
            return "Error: Use a single value, not a list, for '{}'. For multi-component parms use the tuple name.".format(parm_name)

        parm.set(value)
        return "Set {}:{} = {}".format(node_path, parm_name, value)
    except Exception as e:
        return "Error setting parameter: {}".format(str(e))


register_tool(
    name="set_parameter",
    description="Set a parameter value on a Houdini node. "
                "For multi-component parameters (like translate), use tuple names like 't' with a list value. "
                "For single params use names like 'tx', 'ty', 'sx', etc.",
    parameters={
        "node_path": {
            "type": "string",
            "description": "Path to the node (e.g. '/obj/geo1/transform1')",
        },
        "parm_name": {
            "type": "string",
            "description": "Parameter name (e.g. 'tx', 'sy', 'scale', 't' for translate tuple)",
        },
        "value": {
            "type": "string",
            "description": "Value to set. Numbers as strings, or JSON list for tuples.",
        },
    },
    required=["node_path", "parm_name", "value"],
    execute_fn=_set_parameter,
)


# --- set_expression ---

def _set_expression(node_path, parm_name, expression, language="python"):
    try:
        node = hou.node(node_path)
        if node is None:
            return "Error: Node '{}' not found.".format(node_path)

        parm = node.parm(parm_name)
        if parm is None:
            return "Error: Parameter '{}' not found on '{}'.".format(parm_name, node_path)

        lang_map = {"python": hou.exprLanguage.Python, "hscript": hou.exprLanguage.Hscript}
        lang = lang_map.get(language, hou.exprLanguage.Python)

        parm.setExpression(expression, language=lang)
        return "Set expression on {}:{} = {} ({})".format(node_path, parm_name, expression, language)
    except Exception as e:
        return "Error setting expression: {}".format(str(e))


register_tool(
    name="set_expression",
    description="Set an expression on a parameter (Python or HScript).",
    parameters={
        "node_path": {
            "type": "string",
            "description": "Path to the node",
        },
        "parm_name": {
            "type": "string",
            "description": "Parameter name",
        },
        "expression": {
            "type": "string",
            "description": "The expression string",
        },
        "language": {
            "type": "string",
            "description": "Expression language: 'python' or 'hscript'",
        },
    },
    required=["node_path", "parm_name", "expression"],
    execute_fn=_set_expression,
)


# --- get_parameter ---

def _get_parameter(node_path, parm_name):
    try:
        node = hou.node(node_path)
        if node is None:
            return "Error: Node '{}' not found.".format(node_path)

        parm = node.parm(parm_name)
        if parm is None:
            parm_tuple = node.parmTuple(parm_name)
            if parm_tuple is not None:
                vals = [p.eval() for p in parm_tuple]
                return str({"parm": parm_name, "value": vals, "type": "tuple"})
            return "Error: Parameter '{}' not found on '{}'.".format(parm_name, node_path)

        val = parm.eval()
        return str({
            "parm": parm_name,
            "value": val,
            "type": type(val).__name__,
            "expression": parm.expression() if parm.expression() else None,
        })
    except Exception as e:
        return "Error getting parameter: {}".format(str(e))


register_tool(
    name="get_parameter",
    description="Get a parameter's current value from a node. Read-only, no confirmation needed.",
    parameters={
        "node_path": {
            "type": "string",
            "description": "Path to the node",
        },
        "parm_name": {
            "type": "string",
            "description": "Parameter name",
        },
    },
    required=["node_path", "parm_name"],
    execute_fn=_get_parameter,
)


# --- set_keyframe ---

def _set_keyframe(node_path, parm_name, frame, value):
    try:
        node = hou.node(node_path)
        if node is None:
            return "Error: Node '{}' not found.".format(node_path)

        parm = node.parm(parm_name)
        if parm is None:
            return "Error: Parameter '{}' not found on '{}'.".format(parm_name, node_path)

        key = hou.Keyframe()
        key.setFrame(frame)
        key.setValue(value)
        parm.setKeyframe(key)

        return "Keyframed {}:{} at frame {} = {}".format(node_path, parm_name, frame, value)
    except Exception as e:
        return "Error setting keyframe: {}".format(str(e))


register_tool(
    name="set_keyframe",
    description="Set a keyframe on a parameter at a specific frame.",
    parameters={
        "node_path": {
            "type": "string",
            "description": "Path to the node",
        },
        "parm_name": {
            "type": "string",
            "description": "Parameter name to keyframe",
        },
        "frame": {
            "type": "number",
            "description": "Frame number",
        },
        "value": {
            "type": "number",
            "description": "Value at this frame",
        },
    },
    required=["node_path", "parm_name", "frame", "value"],
    execute_fn=_set_keyframe,
)
