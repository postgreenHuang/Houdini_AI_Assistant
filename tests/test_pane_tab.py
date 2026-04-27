"""Test 4: Houdini pane tab / floating window approach"""
from PySide2.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide2.QtCore import Qt
import hou


def make_tab():
    w = QWidget()
    layout = QVBoxLayout(w)
    layout.addWidget(QLabel("Hello AI Assistant!"))
    w.setWindowTitle("Test Tab")
    return w


def test():
    # Try registerViewerPaneTab (Houdini 20.5+)
    if hasattr(hou.ui, "registerViewerPaneTab"):
        hou.ui.registerViewerPaneTab(
            name="test_tab",
            label="Test Tab",
            creator=make_tab,
        )
        print("Pane tab registered! Check pane menu for 'Test Tab'")
    else:
        # Fallback: show as floating window
        parent = hou.qt.mainWindow()
        w = make_tab()
        w.setParent(parent, Qt.Window)
        w.show()
        w.raise_()
        print("Shown as floating window (registerViewerPaneTab not available)")


test()
