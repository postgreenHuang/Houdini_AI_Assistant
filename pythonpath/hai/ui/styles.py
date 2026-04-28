"""QSS Styles — Houdini-inspired dark theme."""

DARK_STYLE = """
QWidget {
    background-color: #2b2b2b;
    color: #d4d4d4;
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 12px;
}

/* Main panels */
QMainWindow, QDialog {
    background-color: #2b2b2b;
}

/* Labels */
QLabel {
    color: #d4d4d4;
    background: transparent;
}

QLabel#titleLabel {
    font-size: 16px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#subtitleLabel {
    font-size: 11px;
    color: #888888;
}

QLabel#contextLabel {
    color: #6ab0f3;
    font-style: italic;
    font-size: 11px;
}

QLabel#tokenLabel {
    color: #888888;
    font-size: 10px;
}

QLabel#statusLabel {
    color: #6ab0f3;
    font-size: 11px;
    font-style: italic;
}

/* Buttons */
QPushButton {
    background-color: #3c3f41;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 14px;
    color: #d4d4d4;
    min-height: 24px;
}

QPushButton:hover {
    background-color: #4a4d4f;
    border-color: #6ab0f3;
}

QPushButton:pressed {
    background-color: #2a6ab0;
}

QPushButton:disabled {
    background-color: #333333;
    color: #666666;
    border-color: #444444;
}

QPushButton#sendButton {
    background-color: #2a6ab0;
    color: white;
    font-weight: bold;
    border: none;
    min-width: 60px;
}

QPushButton#sendButton:hover {
    background-color: #3478c2;
}

QPushButton#sendButton:disabled {
    background-color: #1a4070;
    color: #666666;
}

QPushButton#dangerButton {
    background-color: #a03030;
    color: white;
    border: none;
}

QPushButton#dangerButton:hover {
    background-color: #c04040;
}

/* Text inputs */
QTextEdit, QPlainTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #444444;
    border-radius: 4px;
    color: #d4d4d4;
    padding: 4px;
    selection-background-color: #2a6ab0;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #6ab0f3;
}

QLineEdit {
    background-color: #1e1e1e;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 4px 8px;
    color: #d4d4d4;
}

QLineEdit:focus {
    border-color: #6ab0f3;
}

/* ComboBox */
QComboBox {
    background-color: #3c3f41;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
    color: #d4d4d4;
    min-height: 22px;
}

QComboBox:hover {
    border-color: #6ab0f3;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #2b2b2b;
    border: 1px solid #555555;
    color: #d4d4d4;
    selection-background-color: #2a6ab0;
}

/* CheckBox */
QCheckBox {
    color: #d4d4d4;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #555555;
    background-color: #1e1e1e;
}

QCheckBox::indicator:checked {
    background-color: #2a6ab0;
    border-color: #2a6ab0;
}

/* Scroll area */
QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: #2b2b2b;
    width: 10px;
    border: none;
}

QScrollBar::handle:vertical {
    background: #555555;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #666666;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* Frame separators */
QFrame#separator {
    background-color: #444444;
    max-height: 1px;
}

/* Group boxes */
QGroupBox {
    border: 1px solid #444444;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 12px;
    font-weight: bold;
    color: #aaaaaa;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}

/* Message bubbles */
QFrame#userMessage {
    background-color: #1a3a5c;
    border-radius: 8px;
    padding: 8px;
    margin: 4px 20px 4px 4px;
}

QFrame#assistantMessage {
    background-color: #333333;
    border-radius: 8px;
    padding: 8px;
    margin: 4px 4px 4px 20px;
}

QFrame#errorMessage {
    background-color: #5c1a1a;
    border-radius: 8px;
    padding: 8px;
    margin: 4px;
}

/* Tool bar */
QToolBar {
    background-color: #333333;
    border: none;
    border-bottom: 1px solid #444444;
    padding: 2px;
    spacing: 4px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 8px;
    color: #d4d4d4;
}

QToolButton:hover {
    background-color: #3c3f41;
    border-color: #555555;
}

/* Status bar */
QStatusBar {
    background-color: #333333;
    border-top: 1px solid #444444;
    color: #888888;
    font-size: 10px;
}

/* Tab widget */
QTabWidget::pane {
    border: 1px solid #444444;
    background: #2b2b2b;
}

QTabBar::tab {
    background: #333333;
    border: 1px solid #444444;
    padding: 6px 12px;
    color: #aaaaaa;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background: #2b2b2b;
    color: #ffffff;
    border-bottom-color: #2b2b2b;
}

QTabBar::tab:hover:!selected {
    background: #3c3f41;
}

/* Spin box */
QSpinBox {
    background-color: #1e1e1e;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 4px;
    color: #d4d4d4;
}
"""


def get_stylesheet():
    """Return the dark theme stylesheet."""
    return DARK_STYLE
