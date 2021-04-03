import os
import urllib.request

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QCheckBox, QLineEdit, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout


class Software(QWidget):

    def __init__(self, sh, obj):
        QWidget.__init__(self)

        self.obj = obj
        self.sh = sh

        self.setAutoFillBackground(True)

        self.setStyleSheet("background-color: white;  border-radius: 5; border: 1px solid #EDEDED")

        grid = QGridLayout()

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout()

        self.pic = QLabel()
        self.checked = QCheckBox()
        self.status = QLineEdit()
        self.note = QLineEdit()
        self.fee = QLineEdit()

        self.pic.setStyleSheet("padding: 0; border: none")

        self.checked.setStyleSheet("border: none")
        self.note.setStyleSheet("padding:5")
        self.fee.setStyleSheet("padding:5")

        self.note.setPlaceholderText("Note")
        self.fee.setPlaceholderText("Fee")

        self.pic.setFixedWidth(170)
        self.pic.setFixedHeight(170)
        self.pic.setScaledContents(True)
        pxm = QPixmap()
        pxm.loadFromData(urllib.request.urlopen(obj['thumbnail']).read())
        self.pic.setPixmap(pxm)
        self.pic.setAlignment(Qt.AlignCenter)

        self.status.setDisabled(True)

        if str(self.obj['executable']) == '1':
            # self.checked.setChecked(True)
            self.status.setText("Verified")
            self.status.setStyleSheet("padding: 5;color: lime")
        else:
            self.status.setText("UnVerified")
            self.status.setStyleSheet("padding: 5;color: red")

        if self.obj['note'] is not None:
            self.note.setText("%s" % self.obj['note'])

        if self.obj['price'] is not None:
            self.fee.setText("%s" % self.obj['price'])

        grid.addWidget(self.pic, 0, 0, 1, 10)
        grid.addWidget(self.checked, 1, 0, 1, 1)
        grid.addWidget(self.status, 1, 1, 1, 9)
        grid.addWidget(self.note, 2, 0, 1, 10)
        grid.addWidget(self.fee, 3, 0, 1, 10)

        wrapper.setLayout(grid)
        wrapper_layout.addWidget(wrapper)
        self.setLayout(wrapper_layout)

        # self.checked.clicked.connect(self.test)

    def test(self):

        r = self.sh.app.api.post("/software/%s/test" % self.obj['id'], {"token": self.sh.app.token})
        if r:
            try:
                result = os.popen(r['test_command']).read()
                if result:
                    submit_result = self.sh.app.api.put("/software/%s/test" % self.obj['id'],
                                                        {"token": self.sh.app.token, "result": result})

                    if submit_result['status']:
                        self.status.setText("Verified")
                        return

                self.status.setText("UnVerified")

            except SystemError:
                return None

        pass

    def save(self):
        if self.fee.text():
            return self.sh.app.api.post("/software/%s/item" % self.obj['id'], {"price": self.fee.text(), "note": self.note.text(), "token": self.sh.app.token})
        return False
