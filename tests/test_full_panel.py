"""Test opening the real ChatPanel via Python Panel.

Usage:
    exec(open(r"D:/Projects/HoudiniAIAssistant/tests/test_full_panel.py").read())
"""

import os
import sys

project_root = r"D:/Projects/HoudiniAIAssistant"
pythonpath_dir = os.path.join(project_root, "pythonpath")
if pythonpath_dir not in sys.path:
    sys.path.insert(0, pythonpath_dir)

LOG = os.path.join(project_root, "tests", "crash_log.txt")


def log(step, msg):
    with open(LOG, "w", encoding="utf-8") as f:
        f.write("Step {}: {}\n".format(step, msg))
    print("[Step {}] {}".format(step, msg))


log(1, "import hou")
import hou

log(2, "installFile hai_assistant.pypanel")
pypanel = os.path.join(pythonpath_dir, "python_panels", "hai_assistant.pypanel")
hou.pypanel.installFile(pypanel)

log(3, "interfaceByName hai_assistant")
iface = hou.pypanel.interfaceByName("hai_assistant")

log(4, "createTab PythonPanel")
desktop = hou.ui.curDesktop()
panes = desktop.panes()
pane = panes[0]
tab = pane.createTab(hou.paneTabType.PythonPanel)

log(5, "setActiveInterface — this triggers createInterface() and imports ChatPanel")
tab.setActiveInterface(iface)

log(6, "setIsCurrentTab")
tab.setIsCurrentTab()

log(7, "ALL PASSED — ChatPanel opened in Houdini!")
