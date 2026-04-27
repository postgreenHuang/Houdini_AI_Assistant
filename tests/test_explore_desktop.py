"""Explore Houdini Desktop/Pane/Tab API.

Usage:
    exec(open(r"D:/Projects/HoudiniAIAssistant/tests/test_explore_desktop.py").read())
"""

import hou

desktop = hou.ui.curDesktop()
print("=== Desktop methods ===")
for name in sorted(dir(desktop)):
    if not name.startswith("_"):
        print("  {}".format(name))

print("\n=== Try getting a pane ===")
candidates = ["currentPane", "panes", "paneTabs", "findPane", "paneAt"]
for c in candidates:
    print("  {} : {}".format(c, hasattr(desktop, c)))

# Try the most likely ones
for method_name in ["paneTabs", "panes"]:
    if hasattr(desktop, method_name):
        result = getattr(desktop, method_name)()
        print("\n=== desktop.{}() ===".format(method_name))
        print("  type: {}".format(type(result).__name__))
        print("  count: {}".format(len(result)))
        if result:
            first = result[0]
            print("  first type: {}".format(type(first).__name__))
            pane_methods = [m for m in dir(first) if not m.startswith("_")]
            print("  methods: {}".format(pane_methods))
