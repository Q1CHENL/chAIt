from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QLabel, QDialogButtonBox
)

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
        self.url_input.setPlaceholderText("https://...")
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

        layout.setVerticalSpacing(35)
        layout.addRow("", buttons)

    def get_inputs(self):
        return self.name_input.text().strip(), self.url_input.text().strip()
