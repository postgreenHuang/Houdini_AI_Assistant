"""Minimal Python Panel test — step by step with crash logging.

Usage:
    exec(open(r"D:/Projects/HoudiniAIAssistant/tests/test_minimal_panel.py").read())
"""

import os

LOG = r"D:/Projects/HoudiniAIAssistant/tests/crash_log.txt"


def log(step, msg):
    with open(LOG, "w", encoding="utf-8") as f:
        f.write("Step {}: {}\n".format(step, msg))
    print("[Step {}] {}".format(step, msg))


log(1, "import hou")
import hou

log(2, "installFile minimal .pypanel")
pypanel = r"D:/Projects/HoudiniAIAssistant/tests/test_panel_minimal.pypanel"
hou.pypanel.installFile(pypanel)

log(3, "interfaceByName hai_test")
iface = hou.pypanel.interfaceByName("hai_test")
print("    type={}, value={}".format(type(iface).__name__, iface))

log(4, "get panes")
desktop = hou.ui.curDesktop()
panes = desktop.panes()
print("    {} panes".format(len(panes)))

log(5, "createTab PythonPanel on first pane")
pane = panes[0]
tab = pane.createTab(hou.paneTabType.PythonPanel)
print("    tab type: {}".format(type(tab).__name__))

log(6, "setActiveInterface on tab")
tab.setActiveInterface(iface)

log(7, "setIsCurrentTab")
tab.setIsCurrentTab()

log(8, "ALL PASSED — minimal panel opened successfully!")
