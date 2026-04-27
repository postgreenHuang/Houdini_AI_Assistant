"""Script execution tools — run Python code in Houdini's environment."""

import traceback
import hou
from . import register_tool


def _run_python(code):
    namespace = {"hou": hou, "__builtins__": __builtins__}

    # Track nodes created during execution for post-validation
    _before = _snapshot_child_nodes()

    try:
        exec(code, namespace)
    except Exception:
        return "Error:\n" + traceback.format_exc()

    # Post-execution validation: check for disconnected nodes
    warnings = _check_new_nodes(_before)
    result = "OK"
    if warnings:
        result += "\n" + "\n".join(warnings)
    return result


def _snapshot_child_nodes():
    """Snapshot all child nodes across /obj to detect new ones after execution."""
    snapshot = set()
    try:
        obj = hou.node("/obj")
        if obj:
            for child in obj.allSubChildren():
                snapshot.add(child.path())
    except Exception:
        pass
    return snapshot


def _check_new_nodes(before):
    """Check newly created nodes for issues: disconnected, no output, etc."""
    warnings = []
    try:
        obj = hou.node("/obj")
        if not obj:
            return warnings
        for child in obj.allSubChildren():
            if child.path() in before:
                continue
            # Skip networks and nulls
            try:
                if child.isNetwork() and child.children():
                    continue
            except Exception:
                pass
            node_type = child.type().name()
            # Skip display/render flags nodes — they're supposed to be chain ends
            if node_type in ("null", "out", "output"):
                continue

            # Check: node has no input connections
            has_input = any(inp is not None for inp in child.inputs())
            # Check: node has no output connections
            has_output = len(child.outputConnections()) > 0

            if not has_input and not has_output:
                warnings.append(
                    "WARNING: {} ({}) is completely disconnected — no inputs AND no outputs".format(
                        child.path(), node_type))
            elif not has_output and node_type not in ("null", "out"):
                # Only warn if not the last node in a chain (null would cap it)
                pass

    except Exception:
        pass
    return warnings


register_tool(
    name="run_python",
    description=(
        "Execute Python code in Houdini's environment. "
        "The `hou` module is pre-imported. "
        "Use this for all scene modifications: creating nodes, connecting, "
        "setting parameters, building networks, etc.\n\n"
        "After execution, the system automatically checks for disconnected nodes "
        "and reports warnings. Fix any warnings in a follow-up call.\n\n"
        "MANDATORY two-phase script structure:\n"
        "Phase 1 — Create ALL nodes and wire ALL connections FIRST.\n"
        "Phase 2 — Then set ALL parameters, wrapped in try/except.\n\n"
        "!! CRITICAL: EVERY node (except the first) MUST be connected via setInput().\n"
        "A script that creates nodes without wiring them is BROKEN.\n"
        "N nodes in a chain = N-1 setInput calls. Merges need more.\n"
        "For merge/switch: specify input index — merge.setInput(0, A), merge.setInput(1, B).\n\n"
        "Do NOT mix node creation with parameter setting. "
        "Complete the network topology before touching any parameter."
    ),
    parameters={
        "code": {
            "type": "string",
            "description": (
                "Python script using hou.* API. MUST follow this template:\n\n"
                "geo = hou.node('/obj/geo1')\n"
                "\n"
                "# === PHASE 1: Create & Connect ===\n"
                "box = geo.createNode('box')\n"
                "mountain = geo.createNode('mountain')\n"
                "null = geo.createNode('null')\n"
                "mountain.setInput(0, box)\n"
                "null.setInput(0, mountain)\n"
                "null.moveToGoodPosition()\n"
                "\n"
                "# === PHASE 2: Set Parameters ===\n"
                "errors = []\n"
                "try:\n"
                "    mountain.parm('height').set(2)\n"
                "except Exception as e:\n"
                "    errors.append(f'mountain.height: {e}')\n"
                "try:\n"
                "    mountain.parm('offset').set(0.5)\n"
                "except Exception as e:\n"
                "    errors.append(f'mountain.offset: {e}')\n"
                "\n"
                "# === Report ===\n"
                "print('Created:', box.path(), '->', mountain.path(), '->', null.path())\n"
                "if errors:\n"
                "    print('Parameter errors:')\n"
                "    for e in errors:\n"
                "        print(f'  - {e}')\n"
            ),
        },
    },
    required=["code"],
    execute_fn=_run_python,
)
