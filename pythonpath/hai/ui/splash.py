"""Splash Screen — quick start panel for Houdini AI Assistant."""

from ..qt_compat import (
    Qt, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QApplication,
)
from ..ui.styles import get_stylesheet
from ..config import load_config


class SplashScreen(QWidget):
    """Startup panel with quick access buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Houdini AI Assistant")
        self.setMinimumSize(420, 320)
        self.setStyleSheet(get_stylesheet())
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Houdini AI Assistant")
        title.setObjectName("titleLabel")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #6ab0f3;")
        layout.addWidget(title)

        version = QLabel("v0.1.0")
        version.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(version)

        # Status
        cfg = load_config()
        provider = cfg.get("provider", "")
        has_key = bool(cfg.get("api_keys", {}).get(provider, ""))
        if provider in ("ollama", "lmstudio"):
            has_key = True

        status_text = "Provider: {}".format(provider.upper()) if provider else "Not configured"
        status_color = "#6ab0f3" if has_key else "#e07050"
        self.status_label = QLabel(status_text)
        self.status_label.setStyleSheet("color: {}; font-size: 13px;".format(status_color))
        layout.addWidget(self.status_label)

        layout.addSpacing(8)

        # Quick start buttons
        btn_start = QPushButton("Start Assistant")
        btn_start.setObjectName("sendButton")
        btn_start.setMinimumHeight(40)
        btn_start.setStyleSheet(
            "QPushButton { font-size: 14px; font-weight: bold; }"
        )
        btn_start.clicked.connect(self._start_assistant)
        layout.addWidget(btn_start)

        btn_settings = QPushButton("Settings")
        btn_settings.setMinimumHeight(32)
        btn_settings.clicked.connect(self._open_settings)
        layout.addWidget(btn_settings)

        layout.addSpacing(8)

        # Sample prompts
        samples_label = QLabel("Sample Prompts:")
        samples_label.setStyleSheet("color: #aaa; font-weight: bold;")
        layout.addWidget(samples_label)

        samples = [
            "What nodes do I have selected?",
            "Explain how the selected nodes work together",
            "ACPY: Create a grid with a mountain SOP",
            "Generate a VEX wrangle to add noise displacement",
        ]
        for s in samples:
            btn = QPushButton(s)
            btn.setStyleSheet(
                "QPushButton { text-align: left; padding: 6px 12px; "
                "color: #aaa; font-size: 11px; }"
                "QPushButton:hover { color: #d4d4d4; }"
            )
            btn.clicked.connect(lambda checked, text=s: self._use_sample(text))
            layout.addWidget(btn)

        layout.addStretch()

    def _start_assistant(self):
        from .chat_panel import open_in_pane
        open_in_pane()
        self.close()

    def _open_settings(self):
        from .settings import SettingsDialog
        dlg = SettingsDialog(self)
        if dlg.exec_():
            # Refresh status
            cfg = load_config()
            provider = cfg.get("provider", "")
            self.status_label.setText("Provider: {}".format(provider.upper()))

    def _use_sample(self, text):
        from .chat_panel import open_in_pane
        open_in_pane()
        self.close()
