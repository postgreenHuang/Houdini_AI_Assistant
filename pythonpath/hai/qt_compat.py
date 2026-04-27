"""Qt compatibility layer — auto-detect PySide2 (Houdini <=20.5) or PySide6 (21+)."""

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from PySide6.QtCore import Qt, Signal, Slot
    from PySide6.QtGui import QAction, QFont, QIcon, QPixmap, QColor, QCursor
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
        QCheckBox, QSpinBox, QFileDialog, QMessageBox, QDialog,
        QSplitter, QFrame, QScrollArea, QSizePolicy, QToolButton,
        QStatusBar, QMenuBar, QToolBar, QTabWidget, QTextBrowser,
        QGroupBox, QFormLayout, QSlider, QPlainTextEdit,
    )
    QT_VERSION = 6
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui
    from PySide2.QtCore import Qt, Signal, Slot
    from PySide2.QtGui import QFont, QIcon, QPixmap, QColor, QCursor
    from PySide2.QtWidgets import (
        QAction,
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
        QCheckBox, QSpinBox, QFileDialog, QMessageBox, QDialog,
        QSplitter, QFrame, QScrollArea, QSizePolicy, QToolButton,
        QStatusBar, QMenuBar, QToolBar, QTabWidget, QTextBrowser,
        QGroupBox, QFormLayout, QSlider, QPlainTextEdit,
    )
    QT_VERSION = 5

__all__ = [
    "QtWidgets", "QtCore", "QtGui",
    "Qt", "Signal", "Slot",
    "QAction", "QFont", "QIcon", "QPixmap", "QColor", "QCursor",
    "QApplication", "QMainWindow", "QWidget",
    "QVBoxLayout", "QHBoxLayout",
    "QLabel", "QPushButton", "QLineEdit", "QTextEdit", "QComboBox",
    "QCheckBox", "QSpinBox", "QFileDialog", "QMessageBox", "QDialog",
    "QSplitter", "QFrame", "QScrollArea", "QSizePolicy", "QToolButton",
    "QStatusBar", "QMenuBar", "QToolBar", "QTabWidget", "QTextBrowser",
    "QGroupBox", "QFormLayout", "QSlider", "QPlainTextEdit",
    "QT_VERSION",
]
