import atexit

from PyQt5.QtWidgets import QApplication
from tendo.singleton import SingleInstance

from src.classes.App import App, exit_handler

me = SingleInstance()

if __name__ == '__main__':

    app = QApplication([])
    a = App(app)
    app.exec_()

    atexit.register(exit_handler)
