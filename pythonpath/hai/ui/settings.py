"""Settings Panel — API keys, provider selection, preferences."""

from ..qt_compat import (
    Qt, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
    QCheckBox, QGroupBox, QDialog, QTabWidget, QApplication,
)
from ..ui.styles import get_stylesheet
from ..config import load_config, save_config, DEFAULT_CONFIG


class SettingsDialog(QDialog):
    """Settings dialog for configuring the AI Assistant."""

    PROVIDERS = ["claude", "openai", "deepseek", "gemini", "glm", "ollama", "lmstudio"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Assistant - Settings")
        self.setMinimumSize(500, 550)
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

        # Provider selector
        form = QFormLayout()

        self.provider_combo = QComboBox()
        for p in self.PROVIDERS:
            self.provider_combo.addItem(p.upper(), p)
        current = self._cfg.get("provider", "claude")
        idx = self.PROVIDERS.index(current) if current in self.PROVIDERS else 0
        self.provider_combo.setCurrentIndex(idx)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        form.addRow("Active Provider:", self.provider_combo)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Leave empty for default model")
        self.model_input.setText(self._cfg.get("model", ""))
        form.addRow("Model:", self.model_input)

        layout.addLayout(form)

        # API keys for each provider
        keys_group = QGroupBox("API Keys / URLs")
        keys_layout = QFormLayout(keys_group)

        keys = self._cfg.get("api_keys", {})

        self.key_inputs = {}
        for p in self.PROVIDERS:
            if p in ("ollama", "lmstudio"):
                inp = QLineEdit()
                inp.setPlaceholderText("http://localhost:{}".format("11434" if p == "ollama" else "1234"))
                inp.setText(keys.get(p + "_url", ""))
                self.key_inputs[p] = inp
                keys_layout.addRow("{} URL:".format(p.title()), inp)
            else:
                inp = QLineEdit()
                inp.setEchoMode(QLineEdit.Password)
                inp.setPlaceholderText("Enter {} API Key".format(p.title()))
                inp.setText(keys.get(p, ""))
                self.key_inputs[p] = inp
                keys_layout.addRow("{} Key:".format(p.title()), inp)

        layout.addWidget(keys_group)
        layout.addStretch()
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

        # Code execution
        self.exec_check = QCheckBox("Allow code execution (run_python, run_hscript)")
        self.exec_check.setChecked(self._cfg.get("allow_code_execution", False))
        form.addRow(self.exec_check)

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

    # ---- Events ----

    def _on_provider_changed(self, index):
        provider = self.provider_combo.currentData()
        # Auto-set default model
        defaults = {
            "claude": "claude-sonnet-4-6-20250514",
            "openai": "gpt-4o",
            "deepseek": "deepseek-chat",
            "gemini": "gemini-2.0-flash",
            "glm": "glm-5.1",
            "ollama": "llama3",
            "lmstudio": "local-model",
        }
        if not self.model_input.text():
            self.model_input.setPlaceholderText("Default: {}".format(defaults.get(provider, "")))

    def _save(self):
        cfg = dict(self._cfg)

        cfg["provider"] = self.provider_combo.currentData()
        cfg["model"] = self.model_input.text().strip()
        cfg["system_prompt"] = self.system_prompt.toPlainText().strip()
        cfg["allow_code_execution"] = self.exec_check.isChecked()
        cfg["permission_level"] = self.perm_combo.currentData()
        cfg["language"] = self.lang_combo.currentData()

        try:
            cfg["max_context_nodes"] = int(self.max_nodes.text().strip())
        except ValueError:
            cfg["max_context_nodes"] = 50

        # API keys
        api_keys = cfg.get("api_keys", {})
        for p, inp in self.key_inputs.items():
            if p in ("ollama", "lmstudio"):
                api_keys[p + "_url"] = inp.text().strip()
            else:
                api_keys[p] = inp.text().strip()
        cfg["api_keys"] = api_keys

        save_config(cfg)
        self._cfg = cfg
        self.accept()
