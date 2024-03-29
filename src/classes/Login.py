from os.path import dirname, abspath

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QLineEdit, QPushButton, QDesktopWidget
import webbrowser

from src.api.Pusher import pusher_client


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

        pusherClient = pusher_client()
        email = self.email.text()
        password = self.password.text()

        self.app.api.login(email, password)

        if self.app.api.bearer is not None and self.app.api.bearer != "":
            self.hide()

            if self.app.api.user['role'] == 'rh':
                self.app.rh_screen.show()
                self.app.rh_screen.initializing()
                if not pusherClient.connection.is_alive():
                    self.app.rh_screen.init_pusher()
                else:
                    pusherClient.connect()
            elif self.app.api.user['role'] == 'sh':
                self.app.sh_screen.show()
                self.app.sh_screen.initializing()
                if pusherClient.connection.is_alive():
                    self.app.sh_screen.init_pusher()
                else:
                    pusherClient.connect()

    @staticmethod
    def register(self):
        webbrowser.open("https://calomni.com")

    @staticmethod
    def forgotPW(self, link):
        webbrowser.open(link)
