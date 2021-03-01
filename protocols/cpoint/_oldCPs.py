import numpy as np
# import pynumdiff
import pyqtgraph as pg
from PyQt5 import QtGui, QtWidgets
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d
import popup

ALL = []

# Return False if CP is not evaluated / found correctly


class CPParameter:  # CP parameter class
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


class CPPInt(CPParameter):  # CPPInt inherits CPParameter class
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


class CPPFloat(CPParameter):
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


class CPPCombo(CPParameter):
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


class ContactPoint:  # Contact point class
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

    # def invalidate(self, c, invalid_thresh, j_cp):
    #     y = c._f
    #     for i in y[:j_cp]:
    #         if i-y[j_cp] <= invalid_thresh:
    #             return True

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

            ##Contact Point Finding Algorithms##
#----------------------------------------------------------------------------#


class ThRov(ContactPoint):  # Ratio of Variances
    def create(self):
        self.Fthreshold = CPPFloat('Safe Threshold [nN]')
        self.Fthreshold.setValue(10.0)
        self.Xrange = CPPFloat('X Range [nm]')
        self.Xrange.setValue(1000.0)
        # Window used for RoV calculation
        self.windowr = CPPInt('Window RoV [nm]')
        self.windowr.setValue(200)
        self.addParameter(self.Fthreshold)
        self.addParameter(self.Xrange)
        self.addParameter(self.windowr)

    def getRange(self, c):
        x = c._z
        y = c._f
        try:
            jmax = np.argmin((y - self.Fthreshold.getValue()) ** 2)
            jmin = np.argmin((x - (x[jmax] - self.Xrange.getValue())) ** 2)
        except ValueError:
            return False
        return jmin, jmax

    def getWeight(self, c):
        jmin, jmax = self.getRange(c)
        winr = self.windowr.getValue()
        x = c._z
        y = c._f
        if (winr + jmax) > len(y):  # check1
            return False
        if jmin < winr:  # check2
            return False
        rov = []
        for j in range(jmin, jmax):
            rov.append((np.var(y[j+1: j+winr])) / (np.var(y[j-winr: j-1])))
        return x[jmin:jmax], rov

    def calculate(self, c):
        z = c._z
        f = c._f
        try:
            zz_x, rov = self.getWeight(c)
        except TypeError:
            return
        rov_best_ind = np.argmax(rov)
        j_rov = np.argmin((z-zz_x[rov_best_ind])**2)
        return [z[j_rov], f[j_rov]]


class ThRovFirst(ContactPoint):  # Ratio of variances First peak
    def create(self):
        self.Fthreshold = CPPFloat('Safe Threshold [nN]')  # Force threshold
        self.Fthreshold.setValue(10.0)
        self.Xrange = CPPFloat('X Range [nm]')
        self.Xrange.setValue(1000.0)
        # Window used for RoV calculation
        self.windowr = CPPInt('Window RoV [nm]')
        self.windowr.setValue(200)
        self.addParameter(self.Fthreshold)
        self.addParameter(self.Xrange)
        self.addParameter(self.windowr)

    def getRange(self, c):
        x = c._z
        y = c._f
        try:
            jmax = np.argmin((y - self.Fthreshold.getValue()) ** 2)
            jmin = np.argmin((x - (x[jmax] - self.Xrange.getValue())) ** 2)
        except ValueError:
            return False
        return jmin, jmax

    def getWeight(self, c):
        jmin, jmax = self.getRange(c)
        winr = self.windowr.getValue()
        x = c._z
        y = c._f
        if (len(y) - jmax) < int(winr/2):
            return False
        if (jmin) < int(winr/2):
            return False
        rov = []
        for j in range(jmin, jmax):
            rov.append((np.var(y[j+1: j+winr])) / (np.var(y[j-winr: j-1])))
        return x[jmin:jmax], rov

    def calculate(self, c):
        z = c._z
        f = c._f
        zz_x, rov = self.getWeight(c)
        rov_best_ind = np.argmax(rov)
        j_rov = np.argmin((z-zz_x[rov_best_ind])**2)
        return [z[j_rov], f[j_rov]]


class GoodnessOfFit(ContactPoint):  # Goodness of Fit (GoF)
    def create(self):
        self.windowr = CPPFloat('Window Fit [nm]')
        self.windowr.setValue(200.0)
        self.Xrange = CPPFloat('X Range [nm]')
        self.Xrange.setValue(1000.0)
        self.Fthreshold = CPPFloat('Safe Threshold [nN]')
        self.Fthreshold.setValue(10.0)
        self.addParameter(self.windowr)
        self.addParameter(self.Xrange)
        self.addParameter(self.Fthreshold)

    # Returns min and max indices of f-z data considered
    def getRange(self, c):
        x = c._z
        y = c._f
        try:
            jmax = np.argmin((y - self.Fthreshold.getValue()) ** 2)
            jmin = np.argmin((x - (x[jmax] - self.Xrange.getValue())) ** 2)
        except ValueError:
            return False
        return jmin, jmax

    # Retunrs weight array (R**2) and corresponding index array. Uses get_indentation and fit methods defined below
    def getWeight(self, c):
        jmin, jmax = self.getRange(c)
        if jmin is False or jmax is False:
            return False
        zwin = self.windowr.getValue()
        zstep = (max(c._z) - min(c._z)) / (len(c._z) - 1)
        win = int(zwin / zstep)

        R_squared = []
        j_x = np.arange(jmin, jmax)
        for j in j_x:
            try:
                ind, Yf = self.get_indentation(c, j, win)
                E_std = self.fit(c, ind, Yf)
                R_squared.append(E_std)
            except TypeError:
                return False
        return c._z[jmin:jmax], R_squared

    # Retunrs indentation (ind) and f from z vs f data
    def get_indentation(self, c, iContact, win):
        z = c._z
        f = c._f
        R = c.R
        if (iContact + win) > len(z):
            return False
        Zf = z[iContact: iContact + win] - z[iContact]
        Yf = f[iContact: iContact + win] - f[iContact]
        ind = Zf - Yf / c.k
        ind = ind[ind <= 0.1*R]
        Yf = Yf[ind <= 0.1*R]   # fit only for small indentations
        return ind, Yf

    def fit(self, c, ind, f):
        seeds = [1000.0 / 1e9]
        try:
            R = c.R

            def Hertz(x, E):
                x = np.abs(x)
                poisson = 0.5
                return (4.0 / 3.0) * (E / (1 - poisson ** 2)) * np.sqrt(R * x ** 3)
            popt, pcov = curve_fit(Hertz, ind, f, p0=seeds, maxfev=100000)
            # E_std = np.sqrt(pcov[0][0]) #R**2
            residuals = f - Hertz(ind, *popt)
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((f-np.mean(f))**2)
            R_squared = 1 - (ss_res / ss_tot)
            return R_squared
        except (RuntimeError, ValueError):
            return False

    # Retunrs contact point (z0, f0) based on max R**2
    def calculate(self, c):
        z = c._z
        f = c._f
        try:
            zz_x, R_squared = self.getWeight(c)
        except TypeError:
            return False
        R_best_ind = np.argmax(R_squared)
        j_GoF = np.argmin((z-zz_x[R_best_ind])**2)
        return [z[j_GoF], f[j_GoF]]


class DDer(ContactPoint):  # Second Derivative
    def create(self):
        self.window = CPPInt('Window P [nm]')
        self.window.setValue(20)
        self.Xrange = CPPFloat('X Range [nm]')
        self.Xrange.setValue(1000.0)
        self.Fthreshold = CPPFloat('Safe Threshold [nN]')
        self.Fthreshold.setValue(10.0)
        self.addParameter(self.window)
        self.addParameter(self.Xrange)
        self.addParameter(self.Fthreshold)

    def getRange(self, c):
        x = c._z
        y = c._f
        jmax = np.argmin((y - self.Fthreshold.getValue()) ** 2)
        jmin = np.argmin((x - (x[jmax] - self.Xrange.getValue())) ** 2)
        return jmin, jmax

    def getWeight(self, c):
        jmin, jmax = self.getRange(c)
        if jmin is False:
            return False
        win = self.window.getValue()
        if win % 2 == 0:
            win += 1
        fsecond = savgol_filter(c._f, polyorder=4, deriv=2, window_length=win)
        return c._z[jmin:jmax], fsecond[jmin:jmax]

    def calculate(self, c):
        z = c._z
        f = c._f
        zz_x, ddf = self.getWeight(c)
        ddf_best_ind = np.argmin(ddf)
        jdd = np.argmin((z - zz_x[ddf_best_ind])**2)
        return [c._z[jdd], c._f[jdd]]


class Threshold(ContactPoint):  # Threshold
    def create(self):
        self.Athreshold = CPPFloat('Align Threshold [nN]')
        self.Athreshold.setValue(10.0)
        self.deltaX = CPPFloat('Align left step [nm]')
        self.deltaX.setValue(2000.0)
        self.Fthreshold = CPPFloat('AVG area [nm]')
        self.Fthreshold.setValue(100.0)
        self.addParameter(self.Athreshold)
        self.addParameter(self.deltaX)
        self.addParameter(self.Fthreshold)

    def calculate(self, c):
        yth = self.Athreshold.getValue()
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
        dx = self.deltaX.getValue()
        ddx = self.Fthreshold.getValue()
        if ddx <= 0:
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
        return [x[jcp], y[jcp]]


class Fixed(ContactPoint):  # Threshold
    def create(self):
        self.Zcp = CPPFloat('Position of the CP [nm]')
        self.Zcp.setValue(1000.0)
        self.addParameter(self.Zcp)

    def calculate(self, c):
        xth = self.Zcp.getValue()
        return [xth, c._f[np.argmin((c._z-xth)**2)]]


class PrimeFunction(ContactPoint):  # Prime Function
    def create(self):  # parameters that user inputs in this method for CP calculation
        self.Athreshold = CPPFloat('Align Threshold [nN/nm]')
        self.Athreshold.setValue(0.0005)
        self.deltaX = CPPFloat('Align left step [nm]')
        self.deltaX.setValue(2000.0)
        self.Fthreshold = CPPFloat('AVG area [nm]')
        self.Fthreshold.setValue(100.0)
        self.addParameter(self.Athreshold)
        self.addParameter(self.deltaX)
        self.addParameter(self.Fthreshold)

    def getWeight(self, c):  # weight is the prime function
        z = c._z
        f = c._f
        try:
            win = 31  # arbitrary (insert as input parameter?)
            order = 4  # arbitrary (insert as input parameter?)
            fi = interp1d(z, f)
            zz = np.linspace(min(z), max(z), len(z))
            ff = fi(zz)
            dz = z[1]-z[0]
            dfdz = savgol_filter(ff, win, order, delta=dz,
                                 deriv=1)
            S = dfdz / (1-dfdz)  # c.k in denominator makes it unstable
        except:
            return False
        return z[win:-win], S[win:-win]

    def calculate(self, c):  # calculates CP baed on prime function threshold
        primeth = self.Athreshold.getValue()
        z_False, prime = self.getWeight(c)
        fi = interp1d(c._z, c._f)
        z = np.linspace(min(c._z), max(c._z), len(c._z))
        f = fi(z)
        win = 31
        z = z[win:-win]
        f = f[win:-win]
        if primeth > np.max(prime) or primeth < np.min(prime):
            return False
        jrov = 0
        for j in range(len(prime)-1, 1, -1):
            if prime[j] > primeth and prime[j-1] < primeth:
                jrov = j
                break
        x0 = z[jrov]
        dx = self.deltaX.getValue()
        ddx = self.Fthreshold.getValue()
        if ddx <= 0:
            jxalign = np.argmin((z - (x0 - dx)) ** 2)
            dS0 = prime[jxalign]
        else:
            jxalignLeft = np.argmin((z-(x0-dx-ddx))**2)
            jxalignRight = np.argmin((z-(x0-dx+ddx))**2)
            dS0 = np.average(prime[jxalignLeft:jxalignRight])
        jcp = jrov
        for j in range(jrov, 1, -1):
            if prime[j] > dS0 and prime[j-1] < dS0:
                jcp = j
                break
        return [z[jcp], f[jcp]]
# Second derivative, revisited (prime)


class PrimeFunctionDerivative(ContactPoint):
    def create(self):  # parameters that user inputs in this method for CP calculation
        self.window = CPPInt('Filter/Derivative win [nN/nm]')
        self.window.setValue(51)
        self.order = CPPInt('Filter/Derivative Polynomial Order (Int)')
        self.order.setValue(4)
        self.addParameter(self.window)
        self.addParameter(self.order)

    def getWeight(self, c):
        z = c._z
        f = c._f
        rz = np.linspace(min(z), max(z), len(z))
        rF = np.interp(rz, z, f)
        space = rz[1] - rz[0]
        win = self.window.getValue()
        order = self.order.getValue()
        iwin = int(win/space)
        if iwin % 2 == 0:
            iwin += 1
        if order > iwin:
            return False
        S = savgol_filter(rF, iwin, order, deriv=1, delta=space)
        S = S / (1-S)
        # clean first derivative
        S_clean = savgol_filter(S, iwin*50+1, polyorder=4)  # window length?
        # second derivtive
        ddS = savgol_filter(S_clean, iwin,
                            polyorder=4, deriv=1, delta=space)
        iwin_big = iwin*10  # avoids extrem spikes (arbitrary)
        return rz[iwin_big:-iwin_big], ddS[iwin_big:-iwin_big]

    def calculate(self, c):
        z = c._z
        f = c._f
        rz = np.linspace(min(z), max(z), len(z))
        f = np.interp(rz, z, f)
        space = rz[1] - rz[0]
        win = self.window.getValue()
        order = self.order.getValue()
        iwin = int(win/space)
        if iwin % 2 == 0:
            iwin += 1
        if order > iwin:
            return False
        iwin_big = iwin*5
        z, ddS = self.getWeight(c)
        f = f[iwin_big:-iwin_big]
        best_ind = np.argmax(ddS**2)
        jcp = np.argmin((z - z[best_ind])**2)
        return [z[jcp], f[jcp]]


ALL.append({'label': 'Threshold', 'method': Threshold})
ALL.append({'label': 'Prime Funcion Threshold', 'method': PrimeFunction})
ALL.append({'label': 'Prime Funcion Deriv', 'method': PrimeFunctionDerivative})
ALL.append({'label': 'Gooodness of Fit', 'method': GoodnessOfFit})
ALL.append({'label': 'Ratio of Variances', 'method': ThRov})
ALL.append({'label': 'Ratio of Variances - First Peak', 'method': ThRovFirst})
ALL.append({'label': 'Second derivative', 'method': DDer})
ALL.append({'label': 'Fixed', 'method': Fixed})
