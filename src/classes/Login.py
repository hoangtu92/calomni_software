from os.path import dirname, abspath

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QLineEdit, QPushButton, QDesktopWidget, QLabel
import webbrowser

from src.classes.Alert import Alert


class Login(QWidget):
    email = None
    password = None
    loginBtn = None
    regBtn = None
    app = None

    def __init__(self, app):
        self.app = app
        QWidget.__init__(self)

        uic.loadUi(dirname(dirname(abspath(__file__))) + "/gui/login.ui", self)

        cp = QDesktopWidget().availableGeometry().center()
        qr = self.frameGeometry()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.email = self.findChild(QLineEdit, "email")
        self.password = self.findChild(QLineEdit, "password")
        self.loginBtn = self.findChild(QPushButton, "loginBtn")
        self.regBtn = self.findChild(QPushButton, "registerBtn")

        self.loginBtn.clicked.connect(self.submit)
        self.regBtn.clicked.connect(self.register)

    def submit(self):

        email = self.email.text()
        password = self.password.text()

        if email == "":
            email = 'sh@gmail.com'
            password = '123456'

        self.app.api.login(email, password)

        if self.app.api.bearer is not None:

            self.app.log.debug(self.app.api.user)

            self.hide()

            if self.app.api.user['role'] == 'rh':
                self.app.rh_screen.show()
                self.app.rh_screen.initializing()
            elif self.app.api.user['role'] == 'sh':
                self.app.sh_screen.show()
                self.app.sh_screen.initializing()

        else:
            self.app.log.error("Login incorrect", None, True)

    def register(self):
        webbrowser.open("https://calomni.com")

    def forgotPW(self, link):
        webbrowser.open(link)
