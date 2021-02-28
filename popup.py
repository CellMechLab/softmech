import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets


class uiPanel(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)

        layout = QtWidgets.QVBoxLayout()
        widget = pg.PlotWidget()
        self.p1 = widget.plotItem
        self.p2 = pg.ViewBox()
        self.p1.setLabels(left='FD curve')
        self.p1.showAxis('right')
        self.p1.scene().addItem(self.p2)
        self.p1.getAxis('right').linkToView(self.p2)
        self.p2.setXLink(self.p1)
        self.p1.getAxis('right').setLabel(
            'Weight', color='#ff0000')  # Red (Weight)
        self.p1.getAxis('left').setLabel(
            'FD Curve', color='#0000ff')  # Blue (FD curve)
        self.p1.showGrid(True, True)

        self.updateViews()
        self.p1.vb.sigResized.connect(self.updateViews)

        layout.addWidget(widget)

        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

        self.setWindowTitle("Contact Point Inspection")

        # Handle view resizing

    def updateViews(self):
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
        self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)

    def setPlots(self, x1, y1, x2, y2, x0, y0):
        self.p1.plot(x1, y1, pen=pg.mkPen(
            pg.QtGui.QColor(0, 0, 255, 150), width=5))
        if x0 is not None:
            self.p1.plot([x0], [y0], pen='b', symbol='o')
        self.p2.addItem(pg.PlotCurveItem(x2, y2, pen=pg.mkPen(
            pg.QtGui.QColor(255, 0, 0, 150), width=5)))
