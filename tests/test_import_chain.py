"""Test importing hai modules without crash.

Usage:
    exec(open(r"D:/Projects/HoudiniAIAssistant/tests/test_import_chain.py").read())
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

log(2, "import hai")
import hai

log(3, "from hai.qt_compat import Qt, QWidget")
from hai.qt_compat import Qt, QWidget

log(4, "from hai.config import load_config")
from hai.config import load_config

log(5, "from hai.roles import get_role_names")
from hai.roles import get_role_names

log(6, "from hai.agent import Agent")
from hai.agent import Agent

log(7, "from hai.ui.styles import get_stylesheet")
from hai.ui.styles import get_stylesheet

log(8, "from hai.ui.chat_panel import ChatPanel")
from hai.ui.chat_panel import ChatPanel

log(9, "ALL IMPORTS PASSED")
