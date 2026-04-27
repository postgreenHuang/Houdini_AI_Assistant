"""Confirmation dialog for AI operations."""

from ..qt_compat import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, Qt, QApplication,
)


class ConfirmDialog(QDialog):
    """Dialog showing pending AI operations and asking for confirmation."""

    def __init__(self, operations, parent=None):
        """
        operations: list of (tool_name, description) tuples
        """
        super().__init__(parent)
        self.setWindowTitle("AI Assistant - Confirm Operation")
        self.setMinimumWidth(400)
        self.setMinimumHeight(200)
        self._approved = False

        layout = QVBoxLayout(self)

        # Header
        header = QLabel("AI wants to perform the following operation(s):")
        header.setWordWrap(True)
        header.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        # Operation details
        details = QTextEdit()
        details.setReadOnly(True)
        details.setMaximumHeight(150)
        details.setHtml(self._format_operations(operations))
        layout.addWidget(details)

        # Info
        info = QLabel("All operations support Undo (Ctrl+Z) in Houdini.")
        info.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(info)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_approve = QPushButton("Approve")
        btn_approve.setObjectName("sendButton")
        btn_approve.clicked.connect(self._approve)

        btn_deny = QPushButton("Deny")
        btn_deny.setObjectName("dangerButton")
        btn_deny.clicked.connect(self.reject)

        btn_layout.addWidget(btn_deny)
        btn_layout.addWidget(btn_approve)
        layout.addLayout(btn_layout)

    def _format_operations(self, operations):
        """Format operations list as HTML."""
        html = "<ul>"
        for tool_name, desc in operations:
            html += "<li><b>{}</b>: {}</li>".format(tool_name, desc)
        html += "</ul>"
        return html

    def _approve(self):
        self._approved = True
        self.accept()

    @property
    def approved(self):
        return self._approved
