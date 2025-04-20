from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QLabel, QDialogButtonBox, QVBoxLayout
)
from PyQt6.QtGui import QIcon

class AddSiteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Site")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter site name...")
        self.name_input.setMinimumHeight(36)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("example.com")
        self.url_input.setMinimumHeight(36)

        name_label = QLabel("Name:")
        name_label.setObjectName("dialogLabel")
        url_label = QLabel("URL:")
        url_label.setObjectName("dialogLabel")

        layout.addRow(name_label, self.name_input)
        layout.addRow(url_label, self.url_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setObjectName("dialogButtons")
        # clear default icons and set object names for styling
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn:
            ok_btn.setIcon(QIcon())
            ok_btn.setObjectName("dialogOk")
        cancel_btn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_btn:
            cancel_btn.setIcon(QIcon())
            cancel_btn.setObjectName("dialogCancel")

        layout.setVerticalSpacing(35)
        layout.addRow("", buttons)

    def get_inputs(self):
        return self.name_input.text().strip(), self.url_input.text().strip()

class ConfirmDialog(QDialog):
    """Styled confirmation dialog for removals."""
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setObjectName("confirmButtons")
        # clear default icons and set object names for styling
        yes_btn = buttons.button(QDialogButtonBox.StandardButton.Yes)
        if yes_btn:
            yes_btn.setIcon(QIcon())
            yes_btn.setObjectName("dialogYes")
        no_btn = buttons.button(QDialogButtonBox.StandardButton.No)
        if no_btn:
            no_btn.setIcon(QIcon())
            no_btn.setObjectName("dialogNo")
        layout.addWidget(buttons)
