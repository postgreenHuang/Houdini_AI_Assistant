"""Script execution tools — run Python code in Houdini's environment."""

import traceback
import hou
from . import register_tool


def _run_python(code):
    namespace = {"hou": hou, "__builtins__": __builtins__}

    try:
        exec(code, namespace)
        return "OK"
    except Exception:
        return "Error:\n" + traceback.format_exc()


register_tool(
    name="run_python",
    description=(
        "Execute Python code in Houdini's environment. "
        "The `hou` module is pre-imported. "
        "Use this for all scene modifications: creating nodes, connecting, "
        "setting parameters, building networks, etc.\n\n"
        "MANDATORY two-phase script structure:\n"
        "Phase 1 — Create ALL nodes and wire ALL connections FIRST.\n"
        "Phase 2 — Then set ALL parameters, wrapped in try/except.\n\n"
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
