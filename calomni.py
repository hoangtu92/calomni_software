import atexit
from pathlib import Path

from PyQt5.QtWidgets import QApplication
from src.classes.App import App
from tendo import singleton

# me = singleton.SingleInstance()

if __name__ == '__main__':

    app = QApplication([])
    a = App(app)
    app.exec_()

    atexit.register(a.exit_handler)
