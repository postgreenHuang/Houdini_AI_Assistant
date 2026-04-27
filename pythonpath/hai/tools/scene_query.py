"""Scene query tools — read scene state, selection, node info."""

import hou
from . import register_tool


# --- get_selected_nodes ---

def _get_selected_nodes():
    try:
        nodes = hou.selectedNodes()
        if not nodes:
            return "No nodes selected."

        result = []
        for n in nodes:
            info = {
                "path": n.path(),
                "type": n.type().name(),
                "name": n.name(),
            }
            # Add input connections
            inputs = []
            for i, conn in enumerate(n.inputConnections()):
                inputs.append({
                    "input_index": i,
                    "source": conn.inputNode().path() if conn.inputNode() else None,
                    "source_output": conn.outputIndex(),
                })
            if inputs:
                info["inputs"] = inputs

            # Add outputs
            outputs = []
            for conn in n.outputConnections():
                outputs.append({
                    "output_index": conn.outputIndex(),
                    "dest": conn.outputNode().path() if conn.outputNode() else None,
                    "dest_input": conn.inputIndex(),
                })
            if outputs:
                info["outputs"] = outputs

            result.append(info)

        import json
        return json.dumps(result, indent=2)
    except Exception as e:
        return "Error getting selection: {}".format(str(e))


register_tool(
    name="get_selected_nodes",
    description="Get all currently selected nodes in Houdini. Returns path, type, name, "
                "input/output connections for each. Read-only.",
    parameters={},
    required=[],
    execute_fn=lambda: _get_selected_nodes(),
)


# --- get_node_info ---

def _get_node_info(node_path, include_parms=True):
    try:
        node = hou.node(node_path)
        if node is None:
            return "Error: Node '{}' not found.".format(node_path)

        info = {
            "path": node.path(),
            "name": node.name(),
            "type": node.type().name(),
            "type_category": node.type().category().name() if node.type().category() else "Unknown",
        }

        # Inputs
        inputs = []
        for i, conn in enumerate(node.inputConnections()):
            inputs.append({
                "index": i,
                "source": conn.inputNode().path() if conn.inputNode() else None,
            })
        info["inputs"] = inputs

        # Outputs
        outputs = []
        for conn in node.outputConnections():
            outputs.append({
                "source_output": conn.outputIndex(),
                "dest": conn.outputNode().path() if conn.outputNode() else None,
                "dest_input": conn.inputIndex(),
            })
        info["outputs"] = outputs

        # Parameters
        if include_parms:
            parms = {}
            for parm in node.parms():
                try:
                    val = parm.eval()
                    expr = parm.expression()
                    parms[parm.name()] = {
                        "value": val,
                        "has_expression": bool(expr),
                    }
                except Exception:
                    pass
            info["parameters"] = parms

        # Children (if container)
        children = node.children()
        if children:
            info["children_count"] = len(children)
            info["children"] = [c.name() + " (" + c.type().name() + ")" for c in children[:20]]

        # Comments
        comment = node.comment()
        if comment:
            info["comment"] = comment

        import json
        return json.dumps(info, indent=2, default=str)
    except Exception as e:
        return "Error getting node info: {}".format(str(e))


register_tool(
    name="get_node_info",
    description="Get detailed info about a node: type, parameters, connections, children. Read-only.",
    parameters={
        "node_path": {
            "type": "string",
            "description": "Path to the node",
        },
        "include_parms": {
            "type": "boolean",
            "description": "Include parameter values (default true). Set false for a quick overview.",
        },
    },
    required=["node_path"],
    execute_fn=_get_node_info,
)


# --- get_node_tree ---

def _get_node_tree(parent_path, depth=2):
    try:
        parent = hou.node(parent_path)
        if parent is None:
            return "Error: Node '{}' not found.".format(parent_path)

        def _build_tree(node, current_depth):
            info = {
                "name": node.name(),
                "type": node.type().name(),
                "path": node.path(),
            }
            if current_depth > 0:
                children = node.children()
                if children:
                    info["children"] = [_build_tree(c, current_depth - 1) for c in children]
            return info

        tree = _build_tree(parent, depth)
        import json
        return json.dumps(tree, indent=2)
    except Exception as e:
        return "Error getting node tree: {}".format(str(e))


register_tool(
    name="get_node_tree",
    description="Get the node tree structure starting from a parent path. "
                "depth controls how many levels deep to recurse. Read-only.",
    parameters={
        "parent_path": {
            "type": "string",
            "description": "Path to the root node (e.g. '/obj/geo1')",
        },
        "depth": {
            "type": "integer",
            "description": "Recursion depth (default 2). Use 0 for children only, -1 for unlimited.",
        },
    },
    required=["parent_path"],
    execute_fn=_get_node_tree,
)


# --- list_nodes ---

def _list_nodes(parent_path, type_filter=""):
    try:
        parent = hou.node(parent_path)
        if parent is None:
            return "Error: Node '{}' not found.".format(parent_path)

        children = parent.children()
        if type_filter:
            children = [c for c in children if type_filter.lower() in c.type().name().lower()]

        result = []
        for c in children:
            result.append({
                "name": c.name(),
                "type": c.type().name(),
                "path": c.path(),
            })

        if not result:
            return "No nodes found{}.".format(" matching '{}'".format(type_filter) if type_filter else "")

        import json
        return json.dumps(result, indent=2)
    except Exception as e:
        return "Error listing nodes: {}".format(str(e))


register_tool(
    name="list_nodes",
    description="List child nodes under a parent path. Optional type filter. Read-only.",
    parameters={
        "parent_path": {
            "type": "string",
            "description": "Path to the parent node",
        },
        "type_filter": {
            "type": "string",
            "description": "Optional: filter by node type name (e.g. 'null', 'box')",
        },
    },
    required=["parent_path"],
    execute_fn=_list_nodes,
)


# --- get_scene_info ---

def _get_scene_info():
    try:
        obj = hou.node("/obj")
        if obj is None:
            return "Error: Cannot access /obj context."

        top_nodes = obj.children()
        result = {
            "hip_file": hou.hipFile.path(),
            "frame": hou.frame(),
            "fps": hou.fps(),
            "top_level_objects": [],
        }

        for n in top_nodes[:30]:
            info = {"name": n.name(), "type": n.type().name(), "path": n.path()}
            children = n.children()
            if children:
                info["children_count"] = len(children)
            result["top_level_objects"].append(info)

        import json
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return "Error getting scene info: {}".format(str(e))


register_tool(
    name="get_scene_info",
    description="Get overall scene info: hip file path, current frame, top-level objects. Read-only.",
    parameters={},
    required=[],
    execute_fn=lambda: _get_scene_info(),
)
