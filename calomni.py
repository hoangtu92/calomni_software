import atexit

from PyQt5.QtWidgets import QApplication
from tendo.singleton import SingleInstance

from src.classes.App import App
me = SingleInstance()

if __name__ == '__main__':
    x = me.initialized

    app = QApplication([])
    a = App(app)
    app.exec_()

    atexit.register(a.exit_handler)
