from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel


class Alert(QDialog):

    def __init__(self, message=None, title="Alert"):
        QDialog.__init__(self)
        self.setWindowTitle(title)
        btn = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(btn)
        self.buttonBox.accepted.connect(self.accept)

        self.msg = QLabel()
        self.msg.setText(message)
        self.msg.setFixedHeight(30)

        self.layout = QVBoxLayout()

        self.layout.addWidget(self.msg)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)
        self.exec_()

    def accept(self):
        self.hide()
        pass
