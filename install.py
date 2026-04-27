"""Install script for Houdini AI Assistant.

Usage (in Houdini Python Shell):
    exec(open(r"D:/Projects/HoudiniAIAssistant/install.py").read())
    install(r"D:/Projects/HoudiniAIAssistant")
"""

import os
import sys
import json


def install(project_path=r"D:\Projects\HoudiniAIAssistant"):
    print("=" * 50)
    print("Houdini AI Assistant - Installer")
    print("=" * 50)

    project_root = os.path.normpath(project_path)
    pythonpath_dir = os.path.join(project_root, "pythonpath")

    if not os.path.exists(os.path.join(pythonpath_dir, "hai", "__init__.py")):
        print("ERROR: Cannot find hai package at: {}".format(pythonpath_dir))
        return

    # --- Immediate load ---
    if pythonpath_dir not in sys.path:
        sys.path.insert(0, pythonpath_dir)
    try:
        import hai
        print("import hai -> OK (v{})".format(hai.__version__))
    except ImportError as e:
        print("ERROR: {}".format(e))
        return

    # --- Register for persistent loading ---
    try:
        import hou
        prefs_dir = hou.expandString("$HOUDINI_USER_PREF_DIR")
    except Exception:
        prefs_dir = None

    if not prefs_dir:
        print("Warning: Cannot detect Houdini prefs dir. Session-only load.")
        return

    packages_dir = os.path.join(prefs_dir, "packages")
    if not os.path.exists(packages_dir):
        os.makedirs(packages_dir)

    # Use env to append project root to HOUDINI_PATH.
    # Houdini auto-discovers pythonpath/ under each HOUDINI_PATH entry.
    pkg = {
        "enable": True,
        "env": [
            {
                "HOUDINI_PATH": {
                    "value": project_root.replace("\\", "/"),
                    "method": "append",
                }
            }
        ],
    }

    pkg_path = os.path.join(packages_dir, "HoudiniAIAssistant.json")
    with open(pkg_path, "w", encoding="utf-8") as f:
        json.dump(pkg, f, indent=4)

    print("Package registered: {}".format(pkg_path))
    print("Will auto-load on next Houdini start.")
    print("\nReady! Try: hai.open_assistant()")
    print("=" * 50)


if __name__ == "__main__":
    install()
