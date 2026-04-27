"""Chat Panel — main chat interface embedded as a Houdini Pane Tab."""

import os
import json
import tempfile
import subprocess
import hou
from ..qt_compat import (
    Qt, Signal, QWidget, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QComboBox,
    QFrame, QScrollArea, QSizePolicy, QPlainTextEdit,
    QApplication,
)
from ..ui.styles import get_stylesheet
from ..ui.session_sidebar import SessionSidebar
from ..agent import Agent
from ..roles import get_role_names
from ..config import load_config, save_config
from ..session import create_session, save_session, load_session


class ExternalEditorDialog(QDialog):
    """Open a temp file in system editor (Notepad) for CJK input, then read it back."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("External Editor")
        self.setMinimumWidth(360)
        self.setStyleSheet(get_stylesheet())
        self._text = ""

        # Create temp file
        tmp_dir = tempfile.gettempdir()
        self._filepath = os.path.join(tmp_dir, "hai_input.txt")
        with open(self._filepath, "w", encoding="utf-8") as f:
            f.write("")

        layout = QVBoxLayout(self)

        info = QLabel("An editor window has opened.\n"
                      "Type your message there, save (Ctrl+S), then click **Read & Send** below.")
        info.setWordWrap(True)
        layout.addWidget(info)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self._cleanup_and_reject)
        btn_row.addWidget(btn_cancel)

        btn_send = QPushButton("Read & Send")
        btn_send.setObjectName("sendButton")
        btn_send.setDefault(True)
        btn_send.clicked.connect(self._read_and_accept)
        btn_row.addWidget(btn_send)

        layout.addLayout(btn_row)

        # Open system editor
        self._proc = subprocess.Popen(["notepad", self._filepath])

    def _read_and_accept(self):
        try:
            with open(self._filepath, "r", encoding="utf-8") as f:
                self._text = f.read().strip()
        except Exception:
            self._text = ""
        self._cleanup()
        if self._text:
            self.accept()

    def _cleanup_and_reject(self):
        self._cleanup()
        self.reject()

    def _cleanup(self):
        try:
            self._proc.terminate()
        except Exception:
            pass
        try:
            os.remove(self._filepath)
        except Exception:
            pass

    @property
    def text(self):
        return self._text


class ChatPanel(QWidget):
    """Main AI chat panel for Houdini."""

    _sig_response = Signal(str)
    _sig_tool_call = Signal(str, str)
    _sig_error = Signal(str)
    _sig_done = Signal()
    _sig_token = Signal(int, int)
    _sig_tools_ready = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_processing = False
        self._had_response = False
        self._current_session_id = None

        # UI-only signals (text display, safe cross-thread)
        self._sig_response.connect(self._ui_add_response)
        self._sig_tool_call.connect(self._ui_add_tool_call)
        self._sig_error.connect(self._ui_add_error)
        self._sig_done.connect(self._ui_on_done)
        self._sig_token.connect(self._ui_update_tokens)
        # Tool execution trigger — main thread picks up pending tools
        self._sig_tools_ready.connect(self._ui_execute_tools)

        self.agent = Agent(
            on_response=lambda text: self._sig_response.emit(text),
            on_tool_call=lambda name, args: self._sig_tool_call.emit(name, json.dumps(args, default=str)),
            on_error=lambda msg: self._sig_error.emit(msg),
            on_token_update=lambda i, o: self._sig_token.emit(i, o),
            on_request_done=lambda: self._sig_tools_ready.emit(),
        )
        self._setup_agent()
        self._build_ui()

    # ---- Agent setup ----

    def _setup_agent(self):
        cfg = load_config()
        try:
            self.agent.setup_provider(cfg)
        except Exception:
            pass

    # ---- UI construction ----

    def _build_ui(self):
        self.setStyleSheet(get_stylesheet())

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Session sidebar
        self.sidebar = SessionSidebar(self)
        self.sidebar.session_selected.connect(self._on_session_selected)
        self.sidebar.new_chat_requested.connect(self._new_chat)
        outer.addWidget(self.sidebar)

        # Main chat area
        main = QWidget()
        layout = QVBoxLayout(main)
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

        # Bottom bar
        layout.addWidget(self._build_bottom_bar())

        outer.addWidget(main, 1)

        # Start a new session
        self._new_chat()

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

        # New Chat
        btn_new = QPushButton("+ New Chat")
        btn_new.setToolTip("Start a new conversation")
        btn_new.clicked.connect(self._new_chat)
        layout.addWidget(btn_new)

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

        btn_debug = QPushButton("Debug")
        btn_debug.setToolTip("Debug selected nodes — trace errors upstream")
        btn_debug.clicked.connect(self._debug_selection)
        btn_row.addWidget(btn_debug)

        btn_row.addStretch()

        # Token counter
        self.token_label = QLabel("Tokens: 0 / 0")
        self.token_label.setObjectName("tokenLabel")
        btn_row.addWidget(self.token_label)

        # External editor button (for Chinese/CJK input)
        btn_input = QPushButton("Editor")
        btn_input.setToolTip("Open external editor for CJK / Chinese input")
        btn_input.clicked.connect(self._open_input_dialog)
        btn_row.addWidget(btn_input)

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
        content.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        content.setFrameShape(QFrame.NoFrame)
        content.setStyleSheet("background: transparent; border: none; padding: 0;")
        content.setHtml(self._markdown_to_html(text))
        # Defer height calc to avoid issues during init (width=0)
        self._adjust_text_height(content)
        blayout.addWidget(content)

        self.msg_layout.addWidget(bubble)

        # Auto-scroll (deferred to avoid blocking during init)
        from ..qt_compat import QTimer
        QTimer.singleShot(0, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()))

    def _adjust_text_height(self, content):
        """Set QTextEdit height based on document content."""
        width = self.msg_container.width() - 40
        if width < 100:
            width = 500
        content.document().setTextWidth(width)
        doc_height = content.document().size().height()
        content.setFixedHeight(max(30, int(doc_height) + 10))

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

    # ---- Session management ----

    def _new_chat(self):
        """Start a new conversation session."""
        # Save current session first
        self._save_current_session()
        # Create new session
        self._current_session_id = create_session()
        self.agent.reset()
        self.token_label.setText("Tokens: 0 / 0")
        # Clear messages
        while self.msg_layout.count():
            item = self.msg_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._add_message("assistant",
            "Hello! I'm your Houdini AI Assistant.\n\n"
            "Select nodes and click **Analyze Selection** to let me see your scene, "
            "or just type a question.\n\n"
            "Use **ACPY:** prefix to enter action mode — I'll create and modify nodes for you."
        )
        self.sidebar.refresh(highlight_id=self._current_session_id)

    def _on_session_selected(self, session_id):
        """Load a saved session."""
        if session_id == self._current_session_id:
            return
        self._save_current_session()
        data = load_session(session_id)
        if data is None:
            return
        self._current_session_id = session_id
        # Restore messages
        while self.msg_layout.count():
            item = self.msg_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.agent.set_messages(data.get("messages", []))
        for msg in data.get("messages", []):
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                self._add_message(role, content)
        # Restore tokens
        usage = data.get("token_usage", {})
        self.agent.total_input_tokens = usage.get("input", 0)
        self.agent.total_output_tokens = usage.get("output", 0)
        self.token_label.setText("Tokens: {} in / {} out".format(
            self.agent.total_input_tokens, self.agent.total_output_tokens))
        self.sidebar.refresh(highlight_id=session_id)

    def _save_current_session(self):
        """Auto-save the current session."""
        if not self._current_session_id:
            return
        msgs = self.agent.get_messages()
        if not msgs:
            return
        save_session(
            self._current_session_id,
            msgs,
            token_usage=self.agent.get_token_usage(),
        )

    # ---- Debug ----

    def _debug_selection(self):
        """Analyze selected nodes for errors."""
        if self._is_processing:
            return
        try:
            self.agent.analyze_selection()
            self.ctx_label.setText("Context: Selection")
        except Exception:
            pass
        self._do_send("Debug the selected nodes. Use trace_errors to check for errors and warnings in the upstream chain, then analyze the root cause and suggest fixes.")

    # ---- Actions ----

    def _send_message(self):
        if self._is_processing:
            return
        text = self.input_box.toPlainText().strip()
        if not text:
            return
        self.input_box.clear()
        self._do_send(text)

    def _do_send(self, text):
        """Start agent conversation — state machine handles the rest."""
        self._add_message("user", text)
        self._set_processing(True)
        self.agent.start_conversation(text)

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

    def _open_input_dialog(self):
        """Open external editor (Notepad) for CJK input."""
        if self._is_processing:
            return
        dlg = ExternalEditorDialog(self)
        if dlg.exec_():
            self._do_send(dlg.text)

    def _set_processing(self, active):
        self._is_processing = active
        self._had_response = False
        self.send_btn.setEnabled(not active)
        self.send_btn.setText("Processing..." if active else "Send")

    # ---- Signal slots (called on main thread, safe to update UI) ----

    def _ui_add_response(self, text):
        self._had_response = True
        self._add_message("assistant", text)

    def _ui_add_tool_call(self, tool_name, args_json):
        short = args_json if len(args_json) <= 100 else args_json[:100] + "..."
        self._add_message("assistant", "Calling tool: **{}**({})".format(tool_name, short))

    def _ui_add_error(self, msg):
        frame = QFrame()
        frame.setObjectName("errorMessage")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(8, 6, 8, 6)

        content = QTextEdit()
        content.setReadOnly(True)
        content.setPlainText("Error: " + msg)
        content.setFrameShape(QFrame.NoFrame)
        content.setStyleSheet("background: transparent; border: none; padding: 0;")
        self._adjust_text_height(content)
        fl.addWidget(content)

        self.msg_layout.addWidget(frame)

    def _ui_on_done(self):
        if self.agent._active:
            return  # Still running, don't finalize yet
        self._set_processing(False)
        try:
            self._save_current_session()
        except Exception:
            pass
        try:
            self.sidebar.refresh(highlight_id=self._current_session_id)
        except Exception:
            pass

    def _ui_execute_tools(self):
        """Main thread: execute pending tools, then check if done."""
        if not self.agent._active:
            self._sig_done.emit()
            return
        try:
            self.agent.execute_pending_tools()
        except Exception as e:
            self._ui_add_error("Tool execution error: {}".format(str(e)))
        if not self.agent._active:
            self._sig_done.emit()

    def _ui_update_tokens(self, inp, out):
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
