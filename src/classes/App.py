import hashlib
import os
from pathlib import Path

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget

from src.api.Api import Api
from src.classes.Config import Config
from src.classes.Helper import Helper
from src.classes.Log import Log
from src.classes.Login import Login
from src.classes.RhScreen import RhScreen
from src.classes.ShScreen import ShScreen
from getmac import get_mac_address as gma


class App(QWidget):
    api = None
    login_screen = None
    rh_screen = None
    sh_screen = None
    timer = QTimer()


    def __init__(self, main):
        QWidget.__init__(self)
        self.main = main

        self.timer.setInterval(5000)

        home = str(Path.home())
        self.home_dir = home + "/calomni_software"

        if not os.path.isdir(self.home_dir):
            os.mkdir(self.home_dir)

        if not os.path.isdir(self.home_dir + "/environment/"):
            os.mkdir(self.home_dir + "/environment/")

        if not os.path.isdir(self.home_dir + "/.tmp/"):
            os.mkdir(self.home_dir + "/.tmp/")

        if not os.path.isdir(self.home_dir + "/reports/"):
            os.mkdir(self.home_dir + "/reports/")

        if not os.path.isdir(self.home_dir + "/logs/"):
            os.mkdir(self.home_dir + "/logs/")


        self.api = Api(self)
        self.log = Log(self)
        self.mac = gma()
        if self.mac is None:
            self.log.error("Cannot retrieve mac address. Please make sure your pc has properly setup", None, True, exit)
            return
        self.token = hashlib.md5(self.mac.encode("utf-8")).hexdigest()
        self.log.info("MAC: %s. Token: %s" % (self.mac, self.token))

        self.login_screen = Login(self)
        self.rh_screen = RhScreen(self)
        self.sh_screen = ShScreen(self)

        if self.api.bearer:
            user = self.api.login_bearer()
            if user:
                if user['role'] == 'rh':
                    self.rh_screen.show()
                    self.rh_screen.initializing()
                elif user['role'] == 'sh':
                    self.sh_screen.show()
                    self.sh_screen.initializing()
        else:
            self.login_screen.show()

    def start_timer(self):
        self.timer.start(5000)

    def logout(self):
        Config.save_token("")
        self.exit_handler()
        exit()
        pass

    def exit_handler(self):
        print('Exit application')
        home_dir = str(Path.home()) + "/calomni_software"
        Helper.clear_folder("%s/environment/" % home_dir)
        Helper.clear_folder("%s/.tmp/" % home_dir)
