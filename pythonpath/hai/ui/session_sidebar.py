"""Session sidebar — list, switch, create, delete conversations."""

import os
from ..qt_compat import (
    Qt, Signal, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QFrame, QMenu, QFileDialog, QApplication,
)
from ..ui.styles import get_stylesheet
from ..session import (
    list_sessions, delete_session, export_session, import_session,
)


class SessionSidebar(QFrame):
    """Collapsible sidebar showing conversation history."""

    session_selected = Signal(str)   # session_id
    new_chat_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sessionSidebar")
        self.setFixedWidth(200)
        self.setStyleSheet(get_sidebar_style())
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header: New Chat + Toggle
        header = QHBoxLayout()
        btn_new = QPushButton("+ New")
        btn_new.setObjectName("newChatBtn")
        btn_new.clicked.connect(lambda: self.new_chat_requested.emit())
        header.addWidget(btn_new)
        header.addStretch()
        layout.addLayout(header)

        # Session list
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("sessionList")
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self.list_widget)

        # Bottom buttons: Export / Import
        btn_row = QHBoxLayout()
        btn_export = QPushButton("Export")
        btn_export.clicked.connect(self._export_current)
        btn_row.addWidget(btn_export)

        btn_import = QPushButton("Import")
        btn_import.clicked.connect(self._import_session)
        btn_row.addWidget(btn_import)

        layout.addLayout(btn_row)

    def refresh(self, highlight_id=None):
        """Reload session list from disk."""
        self.list_widget.clear()
        sessions = list_sessions()
        for s in sessions:
            title = s.get("title", "(untitled)") or "(untitled)"
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, s["id"])
            # Tooltip with date
            updated = s.get("updated_at", "")
            if updated:
                item.setToolTip(updated[:16])
            self.list_widget.addItem(item)
            if s["id"] == highlight_id:
                item.setSelected(True)
                self.list_widget.setCurrentItem(item)

    def get_selected_session_id(self):
        item = self.list_widget.currentItem()
        if item:
            return item.data(Qt.UserRole)
        return None

    def _on_item_clicked(self, item):
        session_id = item.data(Qt.UserRole)
        if session_id:
            self.session_selected.emit(session_id)

    def _on_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        session_id = item.data(Qt.UserRole)

        menu = QMenu(self)
        menu.setStyleSheet(get_sidebar_style())
        act_delete = menu.addAction("Delete")
        act_export = menu.addAction("Export to file...")

        action = menu.exec_(self.list_widget.mapToGlobal(pos))
        if action == act_delete:
            delete_session(session_id)
            self.refresh()
        elif action == act_export:
            self._export_by_id(session_id)

    def _export_current(self):
        session_id = self.get_selected_session_id()
        if session_id:
            self._export_by_id(session_id)

    def _export_by_id(self, session_id):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Session", session_id + ".json", "JSON Files (*.json)"
        )
        if path:
            try:
                export_session(session_id, path)
            except Exception as e:
                hou_ui_msg("Export failed: {}".format(str(e)))

    def _import_session(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Session", "", "JSON Files (*.json)"
        )
        if path:
            try:
                new_id = import_session(path)
                self.refresh(highlight_id=new_id)
                self.session_selected.emit(new_id)
            except Exception as e:
                hou_ui_msg("Import failed: {}".format(str(e)))


def hou_ui_msg(msg):
    import hou
    hou.ui.setStatusMessage(msg)


def get_sidebar_style():
    return """
    QFrame#sessionSidebar {
        background: #2a2a2a;
        border-right: 1px solid #444;
    }
    QPushButton#newChatBtn {
        background: #2a6ab0;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 6px 12px;
        font-weight: bold;
    }
    QPushButton#newChatBtn:hover {
        background: #3478c2;
    }
    QListWidget#sessionList {
        background: #2a2a2a;
        border: none;
        color: #ccc;
        font-size: 12px;
        outline: none;
    }
    QListWidget#sessionList::item {
        padding: 8px 6px;
        border-bottom: 1px solid #333;
    }
    QListWidget#sessionList::item:selected {
        background: #3a5a8a;
        color: white;
    }
    QListWidget#sessionList::item:hover {
        background: #353535;
    }
    QPushButton {
        background: #3c3f41;
        border: 1px solid #555;
        border-radius: 3px;
        padding: 4px 8px;
        color: #ccc;
    }
    QPushButton:hover {
        background: #4a4d4f;
    }
    """
