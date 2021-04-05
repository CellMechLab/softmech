import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets

# Plotting pens
PEN_GREEN = pg.mkPen(pg.QtGui.QColor(0, 255, 0, 255), width=2)
ST_RED = 1
ST_BLU = 2
ST_BLK = 3

# Function checking if two arrays are the same



def sames(ar1, ar2):
    if (ar1 is None) or (ar2 is None):
        return False
    if len(ar1) != len(ar2):
        return False
    ar1 = np.array(ar1)
    ar2 = np.array(ar2)
    if np.sum(ar1-ar2) == 0:  # returns true if each element of ar1 is the same as that in ar2
        return True
    return False

# Hertz model with poisson 0.5 (incompressible material)


class Nanoment():
    def __init__(self, curve=None):
        # attributes
        self.basename = None
        self._z = None
        self._f = None
        self._z_raw = None
        self._f_raw = None
        self.R = None
        self.k = None
        self._curve_single = None
        self._curve_raw = None
        self._g_fdistance = None
        self._state = ST_BLK
        self._alpha = 100
        self._selected = False
        self._tree = None
        self._ui = None
        if curve is not None:
            self.R = curve.tip_radius
            self.k = curve.cantilever_k
            self.basename = curve.basename

    # Methods

    def connect(self, nanowin, node=False):
        self._ui = nanowin.ui
        # Plot F(z)
        self._g_fdistance = pg.PlotCurveItem(clickable=True)
        nanowin.ui.g_fdistance.plotItem.addItem(self._g_fdistance)
        self._g_fdistance.sigClicked.connect(nanowin.curve_clicked)
        self._g_fdistance.nano = self

        self._curve_single = nanowin.curve_single
        self._curve_raw = nanowin.curve_raw

        if node is not False:
            self._tree = node
        else:
            myself = QtWidgets.QTreeWidgetItem(nanowin.ui.mainlist)
            myself.setText(0, self.basename)
            myself.curve = self
            myself.setFlags(
                myself.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
            myself.setCheckState(0, QtCore.Qt.Checked)

    def disconnect(self):
        self._g_fdistance = None

        self._tree = None
        self._ui = None
        self._curve_single = None
        self._curve_raw = None

    def update_view(self):
        if self._g_fdistance is not None:
            if self.z is not None and self.force is not None:
                if len(self.z) == len(self.force):
                    self._g_fdistance.setData(self.z, self.force)
                    if self.selected is True:
                        self._curve_raw.setData(self.z_raw, self.f_raw)
                        self._curve_single.setData(self.z, self.force)
            self._g_fdistance.setPen(self.getPen('dist'))

        if self.selected is True:
            if self.active is True:
                self._ui.toggle_activated.setChecked(True)
            else:
                self._ui.toggle_excluded.setChecked(True)

    def getPen(self, curve='ind'):
        PEN_BLACK = pg.mkPen(pg.QtGui.QColor(0, 0, 0, self.alpha), width=1)
        PEN_RED = pg.mkPen(pg.QtGui.QColor(255, 0, 0, self.alpha), width=1)
        PEN_BLUE = pg.mkPen(pg.QtGui.QColor(0, 0, 255, self.alpha), width=1)

        if self.z is None or self.force is None:
            return None
        if len(self.z) != len(self.force):
            return None
        if self.active is True:
            pen = PEN_BLACK
        else:
            pen = PEN_RED
        if self.selected is True:
            pen = PEN_GREEN
        return pen

    def reset_data(self):
        self._z = None
        self._f = None

    def set_XY(self, x, y):
        self.reset_data()
        self._active = True
        self.z_raw = x
        self.f_raw = y

    @ property
    def selected(self):
        return self._selected

    @ selected.setter
    def selected(self, x):
        if x == self._selected:
            return
        self._selected = x
        if x is True:
            self._ui.mainlist.setCurrentItem(self._tree)
        self.update_view()

    @ property
    def alpha(self):
        return self._alpha

    @ alpha.setter
    def alpha(self, x):
        if x == self._alpha:
            return
        self._alpha = x
        self.update_view()

    @ property
    def active(self):
        return self._state == ST_BLK

    @ active.setter
    def active(self, x):
        if x is False:
            self._state = ST_RED
        else:
            self._state = ST_BLK
        self._tree.setCheckState(0, QtCore.Qt.Checked)
        self.update_view()

    @ property
    def z_raw(self):
        return self._z_raw

    @ z_raw.setter
    def z_raw(self, x):
        if x is not None:
            x = np.array(x)
        self._z_raw = x
        self.z = x

    @ property
    def f_raw(self):
        return self._f_raw

    @ f_raw.setter
    def f_raw(self, x):
        if x is not None:
            x = np.array(x)
        self._f_raw = x
        self.force = x

    @ property
    def z(self):
        return self._z

    @ z.setter
    def z(self, x):
        if sames(self._z, x) is False:
            if x is None:
                self._z = None
            else:
                x = np.array(x)
            self._z = x

    @ property
    def force(self):
        return self._f

    @ force.setter
    def force(self, x):
        if sames(self._f, x) is False:
            if x is not None:
                x = np.array(x)
            self._f = x
            self.update_view()