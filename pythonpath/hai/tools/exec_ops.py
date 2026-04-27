"""Script execution tools — run Python code in Houdini's environment."""

import sys
import io
import traceback
import hou
from . import register_tool


def _run_python(code):
    stdout_capture = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_capture

    namespace = {"hou": hou, "__builtins__": __builtins__}

    try:
        exec(code, namespace)
        output = stdout_capture.getvalue()
        result = "OK"
        if output.strip():
            result += "\n--- output ---\n" + output.strip()
        return result
    except Exception:
        error = traceback.format_exc()
        output = stdout_capture.getvalue()
        parts = ["Error:\n", error]
        if output.strip():
            parts.append("\n--- output before error ---\n" + output.strip())
        return "".join(parts)
    finally:
        sys.stdout = old_stdout


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
