from PyQt5.QtWidgets import QApplication
from src.classes.App import App

if __name__ == '__main__':
    app = QApplication([])
    a = App(app)
    app.exec_()





