"""Debug tools — trace errors upstream, analyze node issues."""

import json
import hou
from . import register_tool


def _trace_errors(node_path=""):
    if node_path:
        node = hou.node(node_path)
        if node is None:
            return "Error: Node '{}' not found.".format(node_path)
    else:
        nodes = hou.selectedNodes()
        if not nodes:
            return "No node selected. Select a node or provide a node_path."
        node = nodes[0]

    chain = []
    visited = set()
    _walk_upstream(node, chain, visited, depth=0, max_depth=20)

    if not chain:
        return json.dumps({
            "start": node.path(),
            "status": "No errors or warnings found in upstream chain.",
        }, indent=2)

    return json.dumps({
        "start": node.path(),
        "chain": chain,
        "summary": _summarize(chain),
    }, indent=2, ensure_ascii=False)


def _walk_upstream(node, chain, visited, depth, max_depth):
    if depth > max_depth or node.path() in visited:
        return
    visited.add(node.path())

    info = {
        "path": node.path(),
        "type": node.type().name(),
        "errors": [],
        "warnings": [],
    }

    # Collect errors
    for msg in node.errors():
        info["errors"].append(msg)

    # Collect warnings
    for msg in node.warnings():
        info["warnings"].append(msg)

    # Only include nodes with issues, or the start node
    if info["errors"] or info["warnings"] or depth == 0:
        chain.append(info)

    # Walk upstream
    for inp in node.inputs():
        if inp is not None:
            _walk_upstream(inp, chain, visited, depth + 1, max_depth)


def _summarize(chain):
    errors = sum(len(n["errors"]) for n in chain)
    warnings = sum(len(n["warnings"]) for n in chain)
    parts = []
    if errors:
        parts.append("{} error(s)".format(errors))
    if warnings:
        parts.append("{} warning(s)".format(warnings))
    if not parts:
        return "No issues found."
    return ", ".join(parts) + " in upstream chain."


register_tool(
    name="trace_errors",
    description="Trace errors and warnings from a node upstream through its input chain. "
                "Use this to debug why a node is failing. "
                "Returns a list of nodes with their errors/warnings.",
    parameters={
        "node_path": {
            "type": "string",
            "description": "Path to the node to debug. If empty, uses the currently selected node.",
        },
    },
    required=[],
    execute_fn=_trace_errors,
)
