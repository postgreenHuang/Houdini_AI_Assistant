"""Context builder — serialize scene state for AI consumption."""

import json
import hou


def build_selection_context():
    """Build context from currently selected nodes."""
    nodes = hou.selectedNodes()
    if not nodes:
        return "No nodes currently selected."

    lines = ["## Selected Nodes\n"]
    for n in nodes:
        lines.append(_format_node_compact(n, include_parms=True))

    return "\n".join(lines)


def build_scene_context(max_nodes=50):
    """Build a broad context of the entire scene."""
    lines = [
        "## Scene Context",
        "File: {}".format(hou.hipFile.path()),
        "Frame: {} / FPS: {}".format(hou.frame(), hou.fps()),
    ]

    # Selection
    selected = hou.selectedNodes()
    if selected:
        lines.append("\n### Selected")
        for n in selected[:10]:
            lines.append(_format_node_compact(n, include_parms=True))

    # Top-level obj nodes
    lines.append("\n### /obj Network")
    obj = hou.node("/obj")
    if obj:
        for child in obj.children()[:max_nodes]:
            lines.append(_format_node_compact(child, include_parms=False))
            # Show children inside geo/subnet
            try:
                if child.isNetwork() and child.children():
                    for sub in child.children()[:30]:
                        lines.append("    " + _format_node_compact(sub, include_parms=False))
            except Exception:
                pass

    return "\n".join(lines)


def build_context_for_path(node_path, depth=1):
    """Build context starting from a specific node path."""
    node = hou.node(node_path)
    if node is None:
        return "Node '{}' not found.".format(node_path)

    lines = ["## Node: {}".format(node_path)]
    lines.append(_format_node_compact(node, include_parms=True))

    if depth > 0:
        try:
            children = node.children()
            if children:
                lines.append("\n### Children")
                for c in children[:30]:
                    lines.append("  " + _format_node_compact(c, include_parms=True))
        except Exception:
            pass

    return "\n".join(lines)


def _format_node_compact(node, include_parms=False):
    """Format a node as a single compact line with connection info."""
    type_name = node.type().name()
    name = node.name()
    path = node.path()

    # Build connection string
    inputs = node.inputs()
    inp_parts = []
    for i, inp in enumerate(inputs):
        if inp is not None:
            inp_parts.append("{}<-{}".format(i, inp.name()))

    out_parts = []
    for conn in node.outputConnections():
        dest = conn.outputNode()
        if dest:
            out_parts.append("{}->{}".format(conn.outputIndex(), dest.name()))

    conn_str = ""
    if inp_parts:
        conn_str += " in[" + ", ".join(inp_parts) + "]"
    if out_parts:
        conn_str += " out[" + ", ".join(out_parts) + "]"
    if not inp_parts and not out_parts:
        conn_str = " (disconnected)"

    result = "{} ({}){}".format(name, type_name, conn_str)

    # Add key parameters (only most important ones)
    if include_parms:
        key_parms = _get_key_parms(node)
        if key_parms:
            parm_str = ", ".join(
                "{}={}".format(k, v) for k, v in key_parms.items()
            )
            result += " | " + parm_str

    return result


def _get_key_parms(node):
    """Get a compact dict of the most important parameters."""
    KEY_PARM_NAMES = {
        # Geometry
        "sizex", "sizey", "sizez", "scale", "rad", "rows", "cols",
        "height", "freq", "offset", "dist", "divisions",
        "npoints", "seed",
        # Transform
        "tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz",
        # VEX
        "snippet", "group", "grouptype", "class",
        # Copy
        "ncopies", "input",
        # Display
        "display", "outputidx",
        # Volume
        "voxelsize", "isovalue",
        # Operation
        "operation", "pulldir", "invert",
    }

    parms = {}
    for parm in node.parms():
        name = parm.name()
        if name not in KEY_PARM_NAMES:
            continue
        try:
            val = parm.eval()
            if isinstance(val, float):
                val = round(val, 4)
            parms[name] = val
        except Exception:
            pass

    return parms
