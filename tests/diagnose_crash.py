"""
Houdini AI Assistant - 崩溃诊断脚本 (文件日志版)

使用方法:
  在 Houdini Python Shell 中运行:
    exec(open(r"D:/Projects/HoudiniAIAssistant/tests/diagnose_crash.py").read())

  崩溃后打开这个文件查看最后成功的步骤:
    D:/Projects/HoudiniAIAssistant/tests/crash_log.txt
"""

import os
import sys

LOG_FILE = r"D:/Projects/HoudiniAIAssistant/tests/crash_log.txt"
project_root = r"D:/Projects/HoudiniAIAssistant"
pythonpath_dir = os.path.join(project_root, "pythonpath")

# 确保 hai 包可以被 import
if pythonpath_dir not in sys.path:
    sys.path.insert(0, pythonpath_dir)


def log(step, msg):
    """写入日志并 flush，确保崩溃前内容已落盘。"""
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("Step {}: {}\n".format(step, msg))
    print("[Step {}] {}".format(step, msg))


# ============ 开始诊断 ============

log(1, "import hou ...")
import hou

log(2, "hou.qt.mainWindow() ...")
main_window = hou.qt.mainWindow()

log(3, "import hai ...")
import hai

log(4, "from hai.qt_compat import Qt, QWidget ...")
from hai.qt_compat import Qt, QWidget

log(5, "QWidget() 不带 parent，不 show ...")
w = QWidget()

log(6, "QWidget(main_window) 带 parent，不 show ...")
w = QWidget(main_window)
w = None

log(7, "setParent + Qt.Window 方式，不 show ...")
w = QWidget()
w.setParent(main_window, Qt.Window)
w.setWindowFlags(Qt.Window)
w = None

log(8, "QWidget() 不带 parent，show ...")
w = QWidget()
w.setWindowTitle("Test - no parent")
w.resize(200, 200)
w.show()

log(9, "setParent + Qt.Window 方式，show (shelf 做法) ...")
w = QWidget()
w.setParent(main_window, Qt.Window)
w.setWindowFlags(Qt.Window)
w.setWindowTitle("Test - shelf approach")
w.resize(200, 200)
w.show()

log(10, "QWidget(main_window) 直接 parent，show (__init__.py 当前做法) ... 可能崩溃")
w = QWidget(main_window)
w.setWindowTitle("Test - direct parent")
w.resize(200, 200)
w.show()

log(11, "from hai.ui.splash import SplashScreen ...")
from hai.ui.splash import SplashScreen

log(12, "SplashScreen() 不带 parent ...")
splash = SplashScreen()

log(13, "SplashScreen + setParent + Qt.Window + show (shelf 做法) ...")
splash.setParent(main_window, Qt.Window)
splash.setWindowFlags(Qt.Window)
splash.show()
splash.raise_()

log(14, "SplashScreen(main_window) 直接 parent + show (__init__.py 当前做法) ... 可能崩溃")
splash2 = SplashScreen(main_window)
splash2.show()
splash2.raise_()

log(15, "hai.open_assistant() 实际调用 ... 可能崩溃")
hai.open_assistant()

log(16, "全部通过！没有崩溃。")

# 写入最终结果
with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write("ALL PASSED - no crash detected.\n")
print("\nAll steps passed!")
