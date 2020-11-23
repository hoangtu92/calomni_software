from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel


class Alert(QDialog):

    def __init__(self, message=None, title="Alert", callback=None):
        QDialog.__init__(self)

        self.setWindowTitle(title)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)
        btn = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(btn)
        self.buttonBox.accepted.connect(self.accept)

        self.callback = callback

        self.msg = QLabel()
        self.msg.setText(message)
        self.msg.setFixedHeight(30)

        self.layout = QVBoxLayout()

        self.layout.addWidget(self.msg)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)
        self.exec_()

    def accept(self):
        if self.callback:
            try:
                self.callback()
            except:
                pass
        self.hide()
        pass
