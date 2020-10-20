import hashlib
import os
from pathlib import Path

from PyQt5.QtWidgets import QWidget

from src.api.Api import Api
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

    def __init__(self, main):
        QWidget.__init__(self)
        self.main = main

        home = str(Path.home())
        self.home_dir = home + "/calomni_software"

        if not os.path.isdir(self.home_dir):
            os.mkdir(self.home_dir)

        if not os.path.isdir(self.home_dir + "/environment/"):
            os.mkdir(self.home_dir + "/environment/")

        if not os.path.isdir(self.home_dir + "/reports/"):
            os.mkdir(self.home_dir + "/reports/")

        if not os.path.isdir(self.home_dir + "/logs/"):
            os.mkdir(self.home_dir + "/logs/")

        self.api = Api(self)
        self.log = Log(self)
        self.mac = gma()
        if self.mac is None:
            self.log.error("Cannot retrieve mac address. please make sure your pc has connected to internet")
            return
        self.token = hashlib.md5(self.mac.encode("utf-8")).hexdigest()
        self.log.info("MAC: %s. Token: %s" % (self.mac, self.token))

        self.login_screen = Login(self)
        self.rh_screen = RhScreen(self)
        self.sh_screen = ShScreen(self)
        self.login_screen.show()

