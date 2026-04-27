"""Permission and confirmation system for dangerous operations."""

import hou
from .qt_compat import QMessageBox, QApplication

# Operations that require user confirmation
DANGEROUS_OPERATIONS = {
    "delete_node",
    "run_python",
    "run_hscript",
    "set_parameter",
    "create_node",
    "connect_nodes",
}


def is_read_only(tool_name):
    """Check if a tool only reads data (no side effects)."""
    return tool_name.startswith("get_") or tool_name in ("list_nodes", "search_nodes")


def confirm_operation(tool_name, description):
    """Ask user to confirm a write operation.

    Returns True if approved, False if denied.
    """
    if is_read_only(tool_name):
        return True

    app = QApplication.instance()
    if app is None:
        return True

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Question)
    msg.setWindowTitle("AI Assistant - Confirm Operation")
    msg.setText("AI wants to perform an operation:")
    msg.setInformativeText(
        "Tool: {}\n\n{}".format(tool_name, description)
    )
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.setDefaultButton(QMessageBox.Yes)

    return msg.exec_() == QMessageBox.Yes


def confirm_batch_operations(operations):
    """Confirm a list of operations at once (for ACPY mode).

    operations: list of (tool_name, description) tuples
    Returns True if all approved.
    """
    if not operations:
        return True

    app = QApplication.instance()
    if app is None:
        return True

    details = "\n".join(
        "[{}] {}".format(op[0], op[1]) for op in operations
    )
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("AI Assistant - Batch Operations")
    msg.setText("AI wants to perform {} operations:".format(len(operations)))
    msg.setDetailedText(details)
    msg.setInformativeText(
        "Review the operations below and confirm to proceed.\n"
        "All operations support Undo (Ctrl+Z)."
    )
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.setDefaultButton(QMessageBox.Yes)

    return msg.exec_() == QMessageBox.Yes
