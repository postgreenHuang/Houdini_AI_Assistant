"""Settings Panel — API keys, provider selection, preferences."""

from ..qt_compat import (
    Qt, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
    QCheckBox, QGroupBox, QDialog, QTabWidget, QApplication,
    QScrollArea, QFrame,
)
from ..ui.styles import get_stylesheet
from ..config import load_config, save_config, DEFAULT_CONFIG


class SettingsDialog(QDialog):
    """Settings dialog for configuring the AI Assistant."""

    PROVIDERS = ["claude", "openai", "deepseek", "gemini", "glm", "ollama", "lmstudio", "custom"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Assistant - Settings")
        self.setMinimumSize(550, 600)
        self.setStyleSheet(get_stylesheet())
        self._cfg = load_config()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._build_provider_tab(), "Provider")
        tabs.addTab(self._build_prompt_tab(), "Prompt")
        tabs.addTab(self._build_general_tab(), "General")
        layout.addWidget(tabs)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("Save")
        btn_save.setObjectName("sendButton")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    # ---- Provider tab ----

    def _build_provider_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)

        # Active provider selector (fixed at top)
        top_bar = QWidget()
        top_form = QFormLayout(top_bar)
        top_form.setContentsMargins(8, 8, 8, 4)

        self.provider_combo = QComboBox()
        for p in self.PROVIDERS:
            self.provider_combo.addItem(p.upper(), p)
        current = self._cfg.get("provider", "claude")
        idx = self.PROVIDERS.index(current) if current in self.PROVIDERS else 0
        self.provider_combo.setCurrentIndex(idx)
        top_form.addRow("Active Provider:", self.provider_combo)

        layout.addWidget(top_bar)

        # Scrollable area for provider configs
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(8, 4, 8, 8)
        scroll_layout.setSpacing(8)

        providers_cfg = self._cfg.get("providers", {})
        self._provider_inputs = {}

        for p in self.PROVIDERS:
            defaults = DEFAULT_CONFIG["providers"].get(p, {})
            pcfg = providers_cfg.get(p, {})

            group = QGroupBox(p.upper())
            gform = QFormLayout(group)
            gform.setLabelAlignment(Qt.AlignRight)
            gform.setFormAlignment(Qt.AlignLeft)

            url_input = QLineEdit()
            url_input.setPlaceholderText(defaults.get("url", ""))
            url_input.setText(pcfg.get("url", defaults.get("url", "")))
            gform.addRow("URL:", url_input)

            key_input = QLineEdit()
            key_input.setEchoMode(QLineEdit.Password)
            key_input.setText(pcfg.get("api_key", ""))
            gform.addRow("API Key:", key_input)

            model_input = QLineEdit()
            model_input.setPlaceholderText(defaults.get("model", ""))
            model_input.setText(pcfg.get("model", defaults.get("model", "")))
            gform.addRow("Model:", model_input)

            self._provider_inputs[p] = {
                "url": url_input,
                "api_key": key_input,
                "model": model_input,
            }

            scroll_layout.addWidget(group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)
        return w

    # ---- Prompt tab ----

    def _build_prompt_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        layout.addWidget(QLabel("Custom System Prompt (appended to default):"))

        self.system_prompt = QTextEdit()
        self.system_prompt.setPlaceholderText(
            "Optional: additional instructions for the AI.\n"
            "e.g. 'Always respond in Chinese' or 'Focus on VEX optimization'"
        )
        self.system_prompt.setPlainText(self._cfg.get("system_prompt", ""))
        layout.addWidget(self.system_prompt)

        return w

    # ---- General tab ----

    def _build_general_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        form = QFormLayout()

        # Permission level
        self.perm_combo = QComboBox()
        self.perm_combo.addItem("Confirm each operation", "confirm")
        self.perm_combo.addItem("Allow read-only automatically", "readonly_auto")
        self.perm_combo.addItem("Allow all (dangerous)", "full")
        perm = self._cfg.get("permission_level", "confirm")
        for i in range(self.perm_combo.count()):
            if self.perm_combo.itemData(i) == perm:
                self.perm_combo.setCurrentIndex(i)
                break
        form.addRow("Permission Level:", self.perm_combo)

        # Language
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Chinese", "zh")
        self.lang_combo.addItem("English", "en")
        lang = self._cfg.get("language", "zh")
        self.lang_combo.setCurrentIndex(0 if lang == "zh" else 1)
        form.addRow("UI Language:", self.lang_combo)

        # Max context nodes
        self.max_nodes = QLineEdit()
        self.max_nodes.setText(str(self._cfg.get("max_context_nodes", 50)))
        form.addRow("Max Context Nodes:", self.max_nodes)

        layout.addLayout(form)
        layout.addStretch()
        return w

    # ---- Save ----

    def _save(self):
        cfg = dict(self._cfg)

        cfg["provider"] = self.provider_combo.currentData()
        cfg["system_prompt"] = self.system_prompt.toPlainText().strip()
        cfg["permission_level"] = self.perm_combo.currentData()
        cfg["language"] = self.lang_combo.currentData()

        try:
            cfg["max_context_nodes"] = int(self.max_nodes.text().strip())
        except ValueError:
            cfg["max_context_nodes"] = 50

        # Per-provider config
        providers = {}
        for p, inputs in self._provider_inputs.items():
            providers[p] = {
                "url": inputs["url"].text().strip(),
                "api_key": inputs["api_key"].text().strip(),
                "model": inputs["model"].text().strip(),
            }
        cfg["providers"] = providers

        # Remove old flat format if present
        cfg.pop("api_keys", None)
        cfg.pop("model", None)

        save_config(cfg)
        self._cfg = cfg
        self.accept()
