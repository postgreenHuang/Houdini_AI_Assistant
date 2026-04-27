"""Chat Panel — main chat interface embedded as a Houdini Pane Tab."""

import hou
from ..qt_compat import (
    Qt, Signal, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QComboBox,
    QFrame, QScrollArea, QSizePolicy, QPlainTextEdit,
    QApplication,
)
from ..ui.styles import get_stylesheet
from ..agent import Agent
from ..roles import get_role_names
from ..config import load_config, save_config


class ChatPanel(QWidget):
    """Main AI chat panel for Houdini."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.agent = Agent(
            on_response=self._on_response,
            on_tool_call=self._on_tool_call,
            on_error=self._on_error,
            on_token_update=self._on_token_update,
        )
        self._setup_agent()
        self._build_ui()
        self._is_processing = False

    # ---- Agent setup ----

    def _setup_agent(self):
        cfg = load_config()
        provider = cfg.get("provider", "")
        api_key = ""
        keys = cfg.get("api_keys", {})
        if provider == "ollama":
            api_key = keys.get("ollama_url", "http://localhost:11434")
        elif provider == "lmstudio":
            api_key = keys.get("lmstudio_url", "http://localhost:1234")
        else:
            api_key = keys.get(provider, "")

        if api_key:
            try:
                self.agent.setup_provider(cfg)
            except Exception:
                pass

    # ---- UI construction ----

    def _build_ui(self):
        self.setStyleSheet(get_stylesheet())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar
        layout.addWidget(self._build_top_bar())

        # Message area (scrollable)
        self.msg_container = QWidget()
        self.msg_layout = QVBoxLayout(self.msg_container)
        self.msg_layout.setAlignment(Qt.AlignTop)
        self.msg_layout.setSpacing(4)
        self.msg_layout.setContentsMargins(6, 6, 6, 6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.msg_container)
        scroll.setFrameShape(QFrame.NoFrame)
        layout.addWidget(scroll, 1)
        self.scroll_area = scroll

        # Welcome message
        self._add_message("assistant",
            "Hello! I'm your Houdini AI Assistant.\n\n"
            "Select nodes and click **Analyze Selection** to let me see your scene, "
            "or just type a question.\n\n"
            "Use **ACPY:** prefix to enter action mode — I'll create and modify nodes for you."
        )

        # Bottom bar
        layout.addWidget(self._build_bottom_bar())

    def _build_top_bar(self):
        bar = QFrame()
        bar.setObjectName("topBar")
        bar.setStyleSheet(
            "QFrame#topBar { background: #333333; border-bottom: 1px solid #444; }"
            "QFrame#topBar QPushButton { border: none; padding: 4px 10px; background: transparent; }"
            "QFrame#topBar QPushButton:hover { background: #3c3f41; }"
        )
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 4, 8, 4)

        # Context status
        self.ctx_label = QLabel("Context: None")
        self.ctx_label.setObjectName("contextLabel")
        layout.addWidget(self.ctx_label)

        layout.addStretch()

        # Role selector
        layout.addWidget(QLabel("Role:"))
        self.role_combo = QComboBox()
        for role_id, role_name in get_role_names():
            self.role_combo.addItem(role_name, role_id)
        self.role_combo.currentIndexChanged.connect(self._on_role_changed)
        layout.addWidget(self.role_combo)

        # Clear chat
        btn_clear = QPushButton("Clear")
        btn_clear.setToolTip("Clear conversation history")
        btn_clear.clicked.connect(self._clear_chat)
        layout.addWidget(btn_clear)

        # Settings
        btn_settings = QPushButton("Settings")
        btn_settings.clicked.connect(self._open_settings)
        layout.addWidget(btn_settings)

        return bar

    def _build_bottom_bar(self):
        bar = QWidget()
        layout = QVBoxLayout(bar)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        # Input area
        self.input_box = QPlainTextEdit()
        self.input_box.setPlaceholderText("Type your message... (ACPY: prefix for action mode)")
        self.input_box.setMaximumHeight(80)
        self.input_box.setMinimumHeight(40)
        self.input_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.input_box)

        # Button row
        btn_row = QHBoxLayout()

        btn_analyze_ctx = QPushButton("Analyze Scene")
        btn_analyze_ctx.setToolTip("Send full scene context to AI")
        btn_analyze_ctx.clicked.connect(self._analyze_scene)
        btn_row.addWidget(btn_analyze_ctx)

        btn_analyze_sel = QPushButton("Analyze Selection")
        btn_analyze_sel.setToolTip("Send selected nodes context to AI")
        btn_analyze_sel.clicked.connect(self._analyze_selection)
        btn_row.addWidget(btn_analyze_sel)

        btn_row.addStretch()

        # Token counter
        self.token_label = QLabel("Tokens: 0 / 0")
        self.token_label.setObjectName("tokenLabel")
        btn_row.addWidget(self.token_label)

        # Send button
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("sendButton")
        self.send_btn.clicked.connect(self._send_message)
        self.send_btn.setDefault(True)
        btn_row.addWidget(self.send_btn)

        layout.addLayout(btn_row)
        return bar

    # ---- Message display ----

    def _add_message(self, role, text):
        bubble = QFrame()
        is_user = role == "user"
        bubble.setObjectName("userMessage" if is_user else "assistantMessage")

        blayout = QVBoxLayout(bubble)
        blayout.setContentsMargins(8, 6, 8, 6)

        role_label = QLabel("You" if is_user else "AI Assistant")
        role_label.setStyleSheet(
            "font-size: 10px; font-weight: bold; color: #6ab0f3; background: transparent;"
        )
        blayout.addWidget(role_label)

        content = QTextEdit()
        content.setReadOnly(True)
        content.setFrameShape(QFrame.NoFrame)
        content.setStyleSheet("background: transparent; border: none; padding: 0;")
        # Simple markdown: convert **bold** and newlines
        content.setHtml(self._markdown_to_html(text))
        content.document().setTextWidth(self.msg_container.width() - 40)
        doc_height = content.document().size().height()
        content.setFixedHeight(max(30, int(doc_height) + 10))
        blayout.addWidget(content)

        self.msg_layout.addWidget(bubble)

        # Auto-scroll
        QApplication.processEvents()
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def _markdown_to_html(self, text):
        """Basic markdown-to-HTML conversion."""
        import re
        html = text
        # Bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html)
        # Inline code
        html = re.sub(r'`([^`]+)`', r'<code style="background:#444;padding:1px 4px;border-radius:3px;">\1</code>', html)
        # Code blocks
        html = re.sub(r'```(\w*)\n(.*?)```', r'<pre style="background:#1a1a1a;padding:8px;border-radius:4px;overflow:auto;"><code>\2</code></pre>', html, flags=re.DOTALL)
        # Newlines
        html = html.replace('\n', '<br>')
        return html

    def _clear_chat(self):
        # Remove all message widgets
        while self.msg_layout.count():
            item = self.msg_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.agent.reset()
        self.token_label.setText("Tokens: 0 / 0")
        self._add_message("assistant",
            "Chat cleared. How can I help you?"
        )

    # ---- Actions ----

    def _send_message(self):
        if self._is_processing:
            return
        text = self.input_box.toPlainText().strip()
        if not text:
            return

        self.input_box.clear()
        self._add_message("user", text)

        self._set_processing(True)

        try:
            result = self.agent.send_message(text)
            if result and not self._had_response:
                self._add_message("assistant", result)
        except Exception as e:
            self._add_message("assistant", "Error: {}".format(str(e)))
        finally:
            self._set_processing(False)
            self._had_response = False

    def _analyze_selection(self):
        if self._is_processing:
            return
        try:
            ctx = self.agent.analyze_selection()
            self.ctx_label.setText("Context: Selection")
            self._add_message("assistant", "I can now see your selection. What would you like to do?")
        except Exception as e:
            self._add_message("assistant", "Error analyzing selection: {}".format(str(e)))

    def _analyze_scene(self):
        if self._is_processing:
            return
        try:
            ctx = self.agent.analyze_scene()
            self.ctx_label.setText("Context: Scene")
            self._add_message("assistant", "I can now see your scene. What would you like to do?")
        except Exception as e:
            self._add_message("assistant", "Error analyzing scene: {}".format(str(e)))

    def _on_role_changed(self, index):
        role_id = self.role_combo.currentData()
        self.agent.role = role_id

    def _open_settings(self):
        from .settings import SettingsDialog
        dlg = SettingsDialog(self)
        if dlg.exec_():
            # Reload agent with new config
            self._setup_agent()

    def _set_processing(self, active):
        self._is_processing = active
        self._had_response = False
        self.send_btn.setEnabled(not active)
        self.send_btn.setText("Processing..." if active else "Send")

    # ---- Agent callbacks ----

    def _on_response(self, text):
        self._had_response = True
        self._add_message("assistant", text)

    def _on_tool_call(self, tool_name, args):
        import json
        short = json.dumps(args, default=str)
        if len(short) > 100:
            short = short[:100] + "..."
        self._add_message("assistant", "Calling tool: **{}**({})".format(tool_name, short))

    def _on_error(self, msg):
        frame = QFrame()
        frame.setObjectName("errorMessage")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(8, 6, 8, 6)
        lbl = QLabel("Error: " + msg)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("background: transparent;")
        fl.addWidget(lbl)
        self.msg_layout.addWidget(frame)

    def _on_token_update(self, inp, out):
        self.token_label.setText("Tokens: {} in / {} out".format(inp, out))


# ---- Houdini Python Panel Integration ----

PANEL_INTERFACE_NAME = "hai_assistant"


def create_pane_tab():
    """Create and return a ChatPanel widget. Called by .pypanel createInterface()."""
    panel = ChatPanel()
    panel.setWindowTitle("AI Assistant")
    panel.setMinimumSize(300, 400)
    return panel


def is_registered():
    """Check if the Python Panel interface is available."""
    try:
        hou.pypanel.interfaceByName(PANEL_INTERFACE_NAME)
        return True
    except Exception:
        return False


def _ensure_registered():
    """Ensure the .pypanel interface is loaded. Tries installFile as fallback."""
    if is_registered():
        return True
    # Fallback: manually install the .pypanel file
    try:
        import os
        # __file__ = pythonpath/hai/ui/chat_panel.py → up 3 levels = pythonpath/
        ui_dir = os.path.dirname(os.path.abspath(__file__))   # hai/ui
        hai_dir = os.path.dirname(ui_dir)                      # hai
        pkg_dir = os.path.dirname(hai_dir)                     # pythonpath
        pypanel = os.path.join(pkg_dir, "python_panels", "hai_assistant.pypanel")
        if os.path.exists(pypanel):
            hou.pypanel.installFile(pypanel)
            return is_registered()
    except Exception:
        pass
    return False


def open_in_pane():
    """Open the AI Assistant as a Python Panel tab in the current desktop."""
    if not _ensure_registered():
        hou.ui.setStatusMessage(
            "AI Assistant panel not found.", hou.severityType.Warning,
        )
        return

    iface = hou.pypanel.interfaceByName(PANEL_INTERFACE_NAME)
    desktop = hou.ui.curDesktop()

    # Check if already open — just focus it
    for tab in desktop.paneTabs():
        if tab.type() == hou.paneTabType.PythonPanel:
            try:
                if tab.activeInterface().name() == PANEL_INTERFACE_NAME:
                    tab.setIsCurrentTab()
                    return
            except Exception:
                pass

    # Open in the first pane
    panes = desktop.panes()
    if not panes:
        return
    pane = panes[0]
    tab = pane.createTab(hou.paneTabType.PythonPanel)
    if hasattr(tab, 'setActiveInterface'):
        tab.setActiveInterface(iface)
    tab.setIsCurrentTab()
