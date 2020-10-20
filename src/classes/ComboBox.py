from PyQt5 import QtWidgets, QtCore


class ComboBox(QtWidgets.QComboBox):
    popupAboutToBeShown = QtCore.pyqtSignal()

    def __init__(self):
        QtWidgets.QComboBox.__init__()

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super(ComboBox, self).showPopup()
