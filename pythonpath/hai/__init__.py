"""Houdini AI Assistant - AI Agent plugin for SideFX Houdini."""

__version__ = "0.1.0"
__author__ = "HoudiniAIAssistant"


def open_assistant():
    """Open the AI Assistant chat panel as a Python Panel tab."""
    from .ui.chat_panel import open_in_pane
    open_in_pane()


def show_settings():
    """Open the settings panel."""
    from .ui.settings import SettingsDialog
    import hou
    from .qt_compat import Qt
    parent = hou.qt.mainWindow()
    dlg = SettingsDialog(parent)
    dlg.exec_()
