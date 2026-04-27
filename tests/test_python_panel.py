"""
Houdini AI Assistant - Python Panel 集成测试

使用方法:
  exec(open(r"D:/Projects/HoudiniAIAssistant/tests/test_python_panel.py").read())
"""

import os
import sys

project_root = r"D:/Projects/HoudiniAIAssistant"
pythonpath_dir = os.path.join(project_root, "pythonpath")

if pythonpath_dir not in sys.path:
    sys.path.insert(0, pythonpath_dir)


def test():
    import hou

    # Step 1
    print("[1] hou.pypanel 可用: {}".format(hasattr(hou, "pypanel")))

    # Step 2: 列出已注册接口
    iface_names = hou.pypanel.interfaces()
    print("[2] 已注册接口数量: {}".format(len(iface_names)))
    for name in iface_names:
        print("    - {}".format(name))

    # Step 3: 检查 hai_assistant 是否存在，不存在则 installFile
    found = False
    try:
        iface = hou.pypanel.interfaceByName("hai_assistant")
        found = True
        print("[3] hai_assistant 已注册! type={}, value={}".format(
            type(iface).__name__, iface))
    except Exception:
        print("[3] hai_assistant 未找到，尝试 installFile ...")
        pypanel_file = os.path.join(pythonpath_dir, "python_panels", "hai_assistant.pypanel")
        if os.path.exists(pypanel_file):
            try:
                hou.pypanel.installFile(pypanel_file)
                iface = hou.pypanel.interfaceByName("hai_assistant")
                found = True
                print("    installFile 成功!")
            except Exception as e2:
                print("    installFile 失败: {}".format(e2))
        else:
            print("    .pypanel 文件不存在: {}".format(pypanel_file))

    if not found:
        return

    # Step 4: 在第一个 pane 中创建 Python Panel tab
    print("[4] 创建 Python Panel tab ...")
    try:
        desktop = hou.ui.curDesktop()
        panes = desktop.panes()
        print("    共 {} 个 pane".format(len(panes)))

        # 用第一个 pane
        pane = panes[0]
        tab = pane.createTab(hou.paneTabType.PythonPanel)
        print("    tab 创建成功, type: {}".format(type(tab).__name__))

        # 探测 tab 上 interface 相关方法
        iface_methods = [m for m in dir(tab) if 'interface' in m.lower()]
        print("    interface methods: {}".format(iface_methods))
    except Exception as e:
        print("[4] 失败: {}".format(e))
        return

    # Step 5: 设置 interface 并激活
    print("[5] 设置 interface ...")
    try:
        if hasattr(tab, 'setActiveInterface'):
            tab.setActiveInterface(iface)
            print("    setActiveInterface 成功")
        else:
            print("    无 setActiveInterface, 全部方法:")
            print("    {}".format([m for m in dir(tab) if not m.startswith('_')]))

        tab.setIsCurrentTab(True)
        print("    面板已打开! 检查 Houdini pane 是否出现了 'AI Assistant' 标签页。")
    except Exception as e:
        print("[5] 失败: {}".format(e))


test()
