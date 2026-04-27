"""Context builder — serialize scene state for AI consumption."""

import json
import hou


def build_selection_context():
    """Build context from currently selected nodes."""
    nodes = hou.selectedNodes()
    if not nodes:
        return "No nodes currently selected."

    parts = []
    for n in nodes:
        info = _serialize_node(n, include_parms=True, depth=0)
        parts.append(info)

    return "## Selected Nodes\n\n" + json.dumps(parts, indent=2, default=str)


def build_scene_context(max_nodes=50):
    """Build a broad context of the entire scene."""
    parts = {
        "hip_file": hou.hipFile.path(),
        "frame": hou.frame(),
        "fps": hou.fps(),
        "selection": [],
        "top_level": [],
    }

    # Selection
    selected = hou.selectedNodes()
    for n in selected[:20]:
        parts["selection"].append(_serialize_node(n, include_parms=True, depth=0))

    # Top-level obj nodes
    obj = hou.node("/obj")
    if obj:
        for child in obj.children()[:max_nodes]:
            parts["top_level"].append(_serialize_node(child, include_parms=False, depth=0))

    return "## Scene Context\n\n" + json.dumps(parts, indent=2, default=str)


def build_context_for_path(node_path, depth=1):
    """Build context starting from a specific node path."""
    node = hou.node(node_path)
    if node is None:
        return "Node '{}' not found.".format(node_path)

    info = _serialize_node(node, include_parms=True, depth=depth)
    return "## Node Context\n\n" + json.dumps(info, indent=2, default=str)


def _serialize_node(node, include_parms=True, depth=0):
    """Serialize a single node to a dict."""
    info = {
        "path": node.path(),
        "name": node.name(),
        "type": node.type().name(),
        "category": node.type().category().name() if node.type().category() else "Unknown",
    }

    # Status
    try:
        if node.isNetwork():
            info["is_network"] = True
    except Exception:
        pass

    # Inputs
    inputs = []
    for i in range(len(node.inputs())):
        inp = node.input(i)
        inputs.append({
            "index": i,
            "connected": inp is not None,
            "source": inp.path() if inp else None,
        })
    if inputs:
        info["inputs"] = inputs

    # Outputs
    outputs = []
    for conn in node.outputConnections():
        dest = conn.outputNode()
        outputs.append({
            "output_index": conn.outputIndex(),
            "dest": dest.path() if dest else None,
            "dest_input": conn.inputIndex(),
        })
    if outputs:
        info["outputs"] = outputs

    # Parameters
    if include_parms:
        parms = {}
        for parm in node.parms():
            try:
                val = parm.eval()
                expr = parm.expression()
                if expr:
                    parms[parm.name()] = {"value": val, "expression": expr}
                else:
                    parms[parm.name()] = val
            except Exception:
                pass
        info["parameters"] = parms

    # Comment
    comment = node.comment()
    if comment:
        info["comment"] = comment

    # Children (recursive)
    if depth > 0:
        children = node.children()
        if children:
            info["children"] = [
                _serialize_node(c, include_parms=False, depth=depth - 1)
                for c in children[:30]
            ]

    return info
