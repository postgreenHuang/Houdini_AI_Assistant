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
    description="Execute Python code in Houdini's environment. "
                "The `hou` module is pre-imported. "
                "Use this for all scene modifications: creating nodes, connecting, "
                "setting parameters, building networks, etc. "
                "Generate a COMPLETE script that does everything in one call. "
                "Use Python variables to reference nodes and wire them together.",
    parameters={
        "code": {
            "type": "string",
            "description": "Complete Python script using hou.* API. "
                           "Use variables for node references so you can connect them. "
                           "Example:\n"
                           "geo = hou.node('/obj/geo1')\n"
                           "box = geo.createNode('box')\n"
                           "mountain = geo.createNode('mountain')\n"
                           "mountain.setInput(0, box)\n"
                           "mountain.parm('height').set(2)\n"
                           "null = geo.createNode('null')\n"
                           "null.setInput(0, mountain)\n"
                           "null.moveToGoodPosition()\n"
                           "print('Created:', box.path(), mountain.path(), null.path())",
        },
    },
    required=["code"],
    execute_fn=_run_python,
)
