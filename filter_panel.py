import numpy as np
import pyqtgraph as pg
from PyQt5 import QtGui, QtWidgets
from scipy.signal import savgol_filter, medfilt, detrend
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
import popup

ALL_FILTERS = []

# return False in case of error!


class FilterParameter:  # FilterParameters
    def __init__(self, label=None):
        self._label = label
        self._defaultValue = None
        self._validTypes = ['int', 'float', 'combo']
        self._type = 'int'
        self._values = []
        self._valueLabels = []
        self._widget = None
        self.triggered = None

    def getLabel(self):
        return self._label

    def getWidget(self):
        return self._widget

    def setType(self, t):
        if t in self._validTypes:
            self._type = t

    def setOptions(self, labels, values):
        self.setValueLabels(labels)
        self.setValues(values)

    def setValues(self, v):
        self._values = v

    def setValueLabels(self, v):
        self._valueLabels = v

    def getValue(self):
        pass


class FilterInt(FilterParameter):  # FilterInt
    def __init__(self, label=None):
        super().__init__(label)
        self._defaultValue = 0
        self.setType('int')
        widget = QtWidgets.QLineEdit()
        valid = QtGui.QIntValidator()
        widget.setValidator(valid)
        self._widget = widget
        self.setValue(self._defaultValue)
        self.triggered = self._widget.editingFinished

    def setValue(self, num):
        self._widget.setText(str(int(num)))

    def getValue(self):
        return int(self._widget.text())


class FilterFloat(FilterParameter):  # FilterFloat
    def __init__(self, label=None):
        super().__init__(label)
        self._defaultValue = 0.0
        self.setType('float')
        widget = QtWidgets.QLineEdit()
        valid = QtGui.QDoubleValidator()
        widget.setValidator(valid)
        self._widget = widget
        self.setValue(self._defaultValue)
        self.triggered = self._widget.editingFinished

    def setValue(self, num):
        self._widget.setText(str((num)))

    def getValue(self):
        return float(self._widget.text())


class FilterCombo(FilterParameter):  # FilterCombo
    def __init__(self, label, labels, values):
        super().__init__(label)
        self._defaultValue = 0
        self.setType('combo')

        self._values = values
        self._valueLabels = labels

        widget = QtWidgets.QComboBox()
        for v in labels:
            widget.addItem(v)
        widget.setCurrentIndex(0)
        self._widget = widget
        self.triggered = self._widget.currentIndexChanged

    def getValue(self):
        who = int(self._widget.currentIndex())
        return float(self._values[who])

    def setValue(self, num):
        self._widget.setCurrentIndex(num)


class Filter:  # Filter class
    def __init__(self):
        self._parameters = []
        self.create()

    def create(self):
        pass

    def quickTest(self, c):
        return self.getWeight(c)

    def getWeight(self, c):
        return [1, 2, 3], [2, 6, 4]

    def calculate(self, c):
        pass

    def disconnect(self):
        for p in self._parameters:
            p.triggered.disconnect()

    def connect(self, callback):
        for p in self._parameters:
            p.triggered.connect(callback)

    def addParameter(self, P):
        self._parameters.append(P)

    def createUI(self, layout):
        for i in range(layout.rowCount()):
            layout.removeRow(0)
        for widget in self._parameters:
            layout.addRow(widget.getLabel(), widget.getWidget())


class SavGolFilter(Filter):  # SavGol Filter
    def create(self):
        self.win = FilterInt('Window Length [nm]')
        self.win.setValue(25)
        self.polyorder = FilterInt('Polynomical Order (Int)')
        self.polyorder.setValue(3)
        self.addParameter(self.win)
        self.addParameter(self.polyorder)

    def calculate(self, c):
        y = c._f
        win = self.win.getValue()
        polyorder = self.polyorder.getValue()
        if win % 2 == 0:
            win += 1
        if polyorder > win:
            return None

        y_smooth = savgol_filter(y, win, polyorder)

        return y_smooth


class MedianFilter(Filter):
    def create(self):
        self.win = FilterInt('Window Length [nm]')
        self.win.setValue(25)
        self.addParameter(self.win)

    def calculate(self, c):
        y = c._f
        win = self.win.getValue()
        if win % 2 == 0:
            win += 1
        y_smooth = medfilt(y, win)
        return y_smooth


class DetrendFilter(Filter):  # DetrendFilter

    def calculate(self, c):
        trendline = self.get_trendline(c)
        y_clean = c._f - trendline
        return y_clean

    def get_baseline(self, c):  # returns baseline based on threshold CP method
        yth = 10.0
        x = c._z
        y = c._f
        if yth > np.max(y) or yth < np.min(y):
            return False
        jrov = 0
        for j in range(len(y)-1, 1, -1):
            if y[j] > yth and y[j-1] < yth:
                jrov = j
                break
        x0 = x[jrov]
        dx = 2000.0  # arbitrary
        ddx = 100.0  # arbitrary
        if ddx <= 0:  # useless
            jxalign = np.argmin((x - (x0 - dx)) ** 2)
            f0 = y[jxalign]
        else:
            jxalignLeft = np.argmin((x-(x0-dx-ddx))**2)
            jxalignRight = np.argmin((x-(x0-dx+ddx))**2)
            f0 = np.average(y[jxalignLeft:jxalignRight])
        jcp = jrov
        for j in range(jrov, 1, -1):
            if y[j] > f0 and y[j-1] < f0:
                jcp = j
                break
        if jcp > 2:
            x_base = x[:jcp]
            y_base = y[:jcp]
        else:
            return False
        return x_base, y_base

    def get_trendline(self, c):
        try:
            x_base, y_base = self.get_baseline(c)
        except TypeError:
            return False

        def lin_fit(x, a, b):
            return a*x + b

        popt, pcov = curve_fit(lin_fit, x_base, y_base, maxfev=10000)
        z_lin = np.linspace(min(c._z), max(c._z), len(c._z))
        y_trendline = lin_fit(z_lin, *popt)
        return y_trendline  # calculated over whole z range


ALL_FILTERS.append({'label': 'Savitzky Golay', 'method': SavGolFilter})
ALL_FILTERS.append({'label': 'Median Filter', 'method': MedianFilter})
ALL_FILTERS.append({'label': 'Baseline Detrend', 'method': DetrendFilter})
