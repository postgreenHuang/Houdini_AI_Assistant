"""Node CRUD operations — create, delete, connect, copy/paste nodes."""

import hou
from . import register_tool


def _node_path(node):
    """Safely get node path."""
    try:
        return node.path()
    except Exception:
        return str(node)


def _node_summary(node):
    """Return a brief summary dict for a node."""
    try:
        return {
            "path": node.path(),
            "type": node.type().name(),
            "name": node.name(),
        }
    except Exception as e:
        return {"error": str(e)}


# --- create_node ---

def _create_node(parent_path, node_type, name=""):
    try:
        parent = hou.node(parent_path)
        if parent is None:
            return "Error: Parent path '{}' not found.".format(parent_path)

        # Support type category format like "SOP/box"
        if "/" in node_type:
            parts = node_type.split("/", 1)
            category = parts[0]
            type_name = parts[1]
            node_type_obj = hou.nodeType(hou.nodeCategories().get(category, {}), type_name)
            if node_type_obj is None:
                # Try as relative
                node = parent.createNode(node_type.replace("/", "_"), node_name=name or None)
            else:
                node = node_type_obj.createNode(parent)
                if name:
                    node.setName(name, unique_name=True)
        else:
            node = parent.createNode(node_type, node_name=name or None)

        # Auto-layout
        try:
            node.moveToGoodPosition()
        except Exception:
            pass

        return "Created node: {} (type: {})".format(node.path(), node.type().name())
    except Exception as e:
        return "Error creating node: {}".format(str(e))


register_tool(
    name="create_node",
    description="Create a new node in the Houdini node graph. "
                "parent_path is the container path (e.g. '/obj/geo1'), "
                "node_type is the Houdini node type (e.g. 'box', 'transform', 'null', 'SOP/box'). "
                "name is optional — auto-generated if omitted.",
    parameters={
        "parent_path": {
            "type": "string",
            "description": "Path to the parent node (e.g. '/obj/geo1')",
        },
        "node_type": {
            "type": "string",
            "description": "Node type to create (e.g. 'box', 'null', 'merge', 'blast', 'SOP/box')",
        },
        "name": {
            "type": "string",
            "description": "Optional name for the new node",
        },
    },
    required=["parent_path", "node_type"],
    execute_fn=_create_node,
)


# --- delete_node ---

def _delete_node(node_path):
    try:
        node = hou.node(node_path)
        if node is None:
            return "Error: Node '{}' not found.".format(node_path)
        node.destroy()
        return "Deleted node: {}".format(node_path)
    except Exception as e:
        return "Error deleting node: {}".format(str(e))


register_tool(
    name="delete_node",
    description="Delete a node by its path. This is destructive — confirm with user first.",
    parameters={
        "node_path": {
            "type": "string",
            "description": "Full path to the node to delete (e.g. '/obj/geo1/box1')",
        },
    },
    required=["node_path"],
    execute_fn=_delete_node,
)


# --- connect_nodes ---

def _connect_nodes(source_path, dest_path, input_index=0, output_index=0):
    try:
        source = hou.node(source_path)
        dest = hou.node(dest_path)
        if source is None:
            return "Error: Source node '{}' not found.".format(source_path)
        if dest is None:
            return "Error: Destination node '{}' not found.".format(dest_path)

        dest.setInput(input_index, source, output_index)

        # Auto-layout
        try:
            dest.moveToGoodPosition()
        except Exception:
            pass

        return "Connected {} -> {} (input {})".format(source_path, dest_path, input_index)
    except Exception as e:
        return "Error connecting nodes: {}".format(str(e))


register_tool(
    name="connect_nodes",
    description="Connect two nodes: source output -> destination input. "
                "source_path feeds into dest_path.",
    parameters={
        "source_path": {
            "type": "string",
            "description": "Path of the source (upstream) node",
        },
        "dest_path": {
            "type": "string",
            "description": "Path of the destination (downstream) node",
        },
        "input_index": {
            "type": "integer",
            "description": "Input index on the destination node (default 0)",
        },
        "output_index": {
            "type": "integer",
            "description": "Output index on the source node (default 0)",
        },
    },
    required=["source_path", "dest_path"],
    execute_fn=_connect_nodes,
)


# --- disconnect_node ---

def _disconnect_node(node_path, input_index=0):
    try:
        node = hou.node(node_path)
        if node is None:
            return "Error: Node '{}' not found.".format(node_path)
        node.setInput(input_index, None)
        return "Disconnected input {} of {}".format(input_index, node_path)
    except Exception as e:
        return "Error disconnecting: {}".format(str(e))


register_tool(
    name="disconnect_node",
    description="Disconnect an input of a node.",
    parameters={
        "node_path": {
            "type": "string",
            "description": "Path of the node to disconnect",
        },
        "input_index": {
            "type": "integer",
            "description": "Input index to disconnect (default 0)",
        },
    },
    required=["node_path"],
    execute_fn=_disconnect_node,
)


# --- rename_node ---

def _rename_node(node_path, new_name):
    try:
        node = hou.node(node_path)
        if node is None:
            return "Error: Node '{}' not found.".format(node_path)
        old_name = node.name()
        node.setName(new_name, unique_name=True)
        return "Renamed {} -> {}".format(old_name, node.name())
    except Exception as e:
        return "Error renaming node: {}".format(str(e))


register_tool(
    name="rename_node",
    description="Rename a node.",
    parameters={
        "node_path": {
            "type": "string",
            "description": "Path to the node",
        },
        "new_name": {
            "type": "string",
            "description": "New name for the node",
        },
    },
    required=["node_path", "new_name"],
    execute_fn=_rename_node,
)


# --- copy_node ---

def _copy_node(node_path, new_name=""):
    try:
        node = hou.node(node_path)
        if node is None:
            return "Error: Node '{}' not found.".format(node_path)
        parent = node.parent()
        new_node = hou.copyNodesTo([node], parent)[0]
        if new_name:
            new_node.setName(new_name, unique_name=True)
        try:
            new_node.moveToGoodPosition()
        except Exception:
            pass
        return "Copied node: {} -> {}".format(node_path, new_node.path())
    except Exception as e:
        return "Error copying node: {}".format(str(e))


register_tool(
    name="copy_node",
    description="Copy (duplicate) a node in the same parent.",
    parameters={
        "node_path": {
            "type": "string",
            "description": "Path to the node to copy",
        },
        "new_name": {
            "type": "string",
            "description": "Optional name for the copy",
        },
    },
    required=["node_path"],
    execute_fn=_copy_node,
)
