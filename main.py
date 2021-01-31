import sys

from PySide6 import QtCore, QtGui, QtWidgets

import soft_view as view

class NanoWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        self.ui = view.Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.statusbar.showMessage('Welcome to the SoftMech nanoindentation analysis software')

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('Soft Mech')
    chiaro = NanoWindow()
    chiaro.setWindowTitle('SoftMech')
    chiaro.show()
    QtCore.QObject.connect( app, QtCore.SIGNAL( 'lastWindowClosed()' ), app, QtCore.SLOT( 'quit()' ) )
    sys.exit(app.exec_())
