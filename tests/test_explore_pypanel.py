"""Explore hou.pypanel API — find available methods and attributes.

Usage:
    exec(open(r"D:/Projects/HoudiniAIAssistant/tests/test_explore_pypanel.py").read())
"""

import hou

print("=== hou.pypanel type ===")
print(type(hou.pypanel))

print("\n=== hou.pypanel methods ===")
for name in sorted(dir(hou.pypanel)):
    if not name.startswith("_"):
        attr = getattr(hou.pypanel, name)
        print("  {} : {}".format(name, type(attr).__name__))

print("\n=== Try common method names ===")
candidates = [
    "interfaces", "interfacesByName", "interfaceByName",
    "registeredInterfaces", "getInterfaces", "allInterfaces",
    "findInterface", "getInterface", "panelInterfaces",
]
for name in candidates:
    has = hasattr(hou.pypanel, name)
    print("  {} : {}".format(name, has))

# Also check hou.ui for pane-tab related methods
print("\n=== hou.ui pane/pypanel methods ===")
for name in sorted(dir(hou.ui)):
    if "pane" in name.lower() or "panel" in name.lower() or "tab" in name.lower():
        print("  hou.ui.{} : {}".format(name, type(getattr(hou.ui, name)).__name__))

# Check hou.paneTabType values
print("\n=== hou.paneTabType ===")
for name in sorted(dir(hou.paneTabType)):
    if not name.startswith("_"):
        print("  {}".format(name))
