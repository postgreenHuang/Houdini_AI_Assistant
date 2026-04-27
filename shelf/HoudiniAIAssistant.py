"""Houdini AI Assistant — Shelf tool loader.

Usage in Houdini Python Shell:
    import hai
    hai.open_assistant()

Or add to HOUDINI_PATH/pythonpath and use the Shelf button.
"""

import hou


def open_assistant():
    """Open the AI Assistant chat panel as a Python Panel tab."""
    from hai.ui.chat_panel import open_in_pane
    open_in_pane()


def show_settings():
    """Open settings dialog as a Python Panel tab."""
    try:
        iface = hou.pypanel.interfaceByName("hai_settings")
    except Exception:
        iface = None

    if iface is not None:
        desktop = hou.ui.curDesktop()
        panes = desktop.panes()
        if not panes:
            return
        pane = panes[0]
        tab = pane.createTab(hou.paneTabType.PythonPanel)
        tab.setActiveInterface(iface)
        tab.setIsCurrentTab()
    else:
        # Fallback: dialog
        from hai.ui.settings import SettingsDialog
        from hai.qt_compat import Qt
        parent = hou.qt.mainWindow()
        dlg = SettingsDialog(parent)
        dlg.exec_()
