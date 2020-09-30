import hashlib
from pathlib import Path

from PyQt5.QtWidgets import QWidget

from src.api.Api import Api
from src.classes.Login import Login
from src.classes.RhScreen import RhScreen
from src.classes.ShScreen import ShScreen
from getmac import get_mac_address as gma


class App(QWidget):
    api = None
    login_screen = None
    rh_screen = None
    sh_screen = None

    def __init__(self):
        QWidget.__init__(self)
        self.mac = gma()
        self.token = hashlib.md5(self.mac.encode("utf-8")).hexdigest()
        print("MAC: %s. Token: %s" % (self.mac, self.token))

        home = str(Path.home())
        self.home_dir = home + "/calomni_software"

        self.api = Api()
        self.login_screen = Login(self)
        self.rh_screen = RhScreen(self)
        self.sh_screen = ShScreen(self)
        # self.sh_screen.show()
        self.login_screen.show()

        # print("%s %s" % (platform.platform(), os.system("lsb_release -a")))


