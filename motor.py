import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit
from scipy.signal import find_peaks, savgol_filter

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


def hertz(x, E, R, poisson=0.5):
    return (4.0 / 3.0) * (E / (1 - poisson ** 2)) * np.sqrt(R * x ** 3)

# Gauss function


def Gauss(x, x0, w, A):
    return A*np.exp(-((x-x0)/w)**2)

# Calculation of Hertz model:
# returns x (indentation), y (force), z (cantilever displacement)


def calc_hertz(E, R, k, maxvalue):
    x = np.linspace(0, maxvalue, int(maxvalue))
    y = hertz(x, E/1e9, R)
    z = x + y/k
    return x, y, z

# Calculating gaussian fit
# returns peak centre (x0), width (w), amp (A), nx (range), Gaussian fit computed with optimal parameters (Gauss(nx, *popt))


def gauss_fit(x, y):
    if len(x) == len(y)+1:
        x = (x[1:]+x[:-1])/2.0
    popt, pcov = curve_fit(Gauss, x, y, p0=[x[np.argmax(
        y)], (np.max(x)-np.min(x))/10.0, np.max(y)], maxfev=1000)
    nx = np.linspace(np.min(x), np.max(x), 100)
    x0, w, A = popt
    return x0, w, A, nx, Gauss(nx, *popt)


class Nanoment():
    def __init__(self, curve=None):
        # attributes
        self.basename = None
        self._contactpoint = [0, 0]
        self._z = None
        self._f = None
        self._z_raw = None
        self._f_raw = None
        self._ind = None
        self._touch = None
        self.R = None
        self.k = None
        self._E = 5
        self._ex = None
        self._ey = None
        self._curve_single = None
        self._curve_raw = None
        self._curve_fit = None
        self._g_fdistance = None
        self._g_indentation = None
        self._g_scatter = None
        self._state = ST_BLK = 3
        self._alpha = 100
        self._selected = False
        self._tree = None
        self._ui = None
        self._Eindex = 0
        self._cpfunction = None
        self._filter = None
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
        # Plot F(delta)
        self._g_indentation = pg.PlotCurveItem(clickable=True)
        nanowin.ui.g_indentation.plotItem.addItem(self._g_indentation)
        self._g_indentation.sigClicked.connect(nanowin.curve_clicked)
        self._g_indentation.nano = self
        # Plot E(delta)
        self._g_es = pg.PlotCurveItem(clickable=True)
        nanowin.ui.g_es.plotItem.addItem(self._g_es)
        self._g_es.sigClicked.connect(nanowin.curve_clicked)
        self._g_es.nano = self
        # Plot E
        self._g_scatter = pg.PlotDataItem(
            clickable=True, pen=None, symbol='o', symbolPen=None, symbolBrush=None)
        self._Eindex = len(nanowin.ui.g_scatter.plotItem.items)
        self._g_scatter.setSymbolPen(None)
        self._g_scatter.setSymbolBrush(None)
        nanowin.ui.g_scatter.plotItem.addItem(self._g_scatter)
        self._g_scatter.sigClicked.connect(nanowin.curve_clicked)
        self._g_scatter.nano = self

        self._curve_single = nanowin.curve_single
        self._curve_raw = nanowin.curve_raw
        self._curve_fit = nanowin.curve_fit

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
        self._g_indentation = None
        self._g_scatter = None

        self._g_es = None

        self._tree = None
        self._ui = None
        self._curve_single = None
        self._curve_raw = None
        self._curve_fit = None
        self._cpfunction = None

    def update_view(self):
        if self._g_fdistance is not None:
            if self.z is not None and self.force is not None:
                if len(self.z) == len(self.force):
                    self._g_fdistance.setData(self.z, self.force)
                    if self.selected is True:
                        self._curve_raw.setData(self.z_raw, self.f_raw)
                        self._curve_single.setData(self.z, self.force)
                        if self.E is not None:
                            ex, ey = self.getFitted()
                            self._curve_fit.setData(ex, ey)
                        else:
                            self._curve_fit.setData(None)
            self._g_fdistance.setPen(self.getPen('dist'))

        if self._g_indentation is not None:
            if self.ind is not None and self.touch is not None:
                if len(self.ind) == len(self.touch):
                    self._g_indentation.setData(self.ind, self.touch)
            self._g_indentation.setPen(self.getPen('ind'))

        if self._g_es is not None:
            if self.Ex is not None and self.Ey is not None:
                if len(self.Ex) == len(self.Ey):
                    self._g_es.setData(self.Ex**2/self.R, self.Ey*1e9)
                    self._g_es.setPen(self.getPen('es'))

            else:
                self._g_es.setPen(None)

        if self._g_scatter is not None:
            if self.active is True and self.E is not None:
                self._g_scatter.setData(x=[self._Eindex], y=[self.E])
                self._g_scatter.setSymbolPen('k')
                self._g_scatter.setSymbolBrush('b')
            else:
                self._g_scatter.setSymbolPen(None)
                self._g_scatter.setSymbolBrush(None)

        if self.selected is True:
            self._ui.stats_R.setText(str(self.R))
            self._ui.stats_k.setText(str(self.k))
            if self.active is True:
                self._ui.toggle_activated.setChecked(True)
                if self.E is not None:
                    self._g_scatter.setSymbolPen(PEN_GREEN)
            elif self.included is False:
                self._ui.toggle_excluded.setChecked(True)
            else:
                self._ui.toggle_included.setChecked(True)

    def getPen(self, curve='ind'):
        PEN_BLACK = pg.mkPen(pg.QtGui.QColor(0, 0, 0, self.alpha), width=1)
        PEN_RED = pg.mkPen(pg.QtGui.QColor(255, 0, 0, self.alpha), width=1)
        PEN_BLUE = pg.mkPen(pg.QtGui.QColor(0, 0, 255, self.alpha), width=1)

        if curve == 'ind':
            if self.ind is None or self.touch is None:
                return None
            if len(self.ind) != len(self.touch):
                return None
            if self.active is False:
                return None
            pen = PEN_BLACK
        elif curve == 'es':
            if self.Ex is None or self.Ey is None:
                return None
            if len(self.Ex) != len(self.Ey):
                return None
            if self.active is False:
                return None
            pen = PEN_BLACK
        else:
            if self.z is None or self.force is None:
                return None
            if len(self.z) != len(self.force):
                return None
            if self.active is True:
                pen = PEN_BLACK
            else:
                if self.included is True:
                    pen = PEN_BLUE
                else:
                    pen = PEN_RED
        if self._ui.view_all.isChecked() is False and self.active is False:
            if self._ui.view_active.isChecked() is True:
                if self.active is False:
                    pen = None
            else:
                if self.included is False:
                    pen = None
        if self.selected is True:
            pen = PEN_GREEN
        return pen

    def setFilterFunction(self, cf):
        self._filter = cf

    def setCPFunction(self, cf):
        self._cpfunction = cf

    def set_elasticityspectra(self):
        if self._ui.es_analysis.isChecked() is False:
            return
        if self.k is None:
            return
        if self. active is False:
            return
        if self.ind is None or self.touch is None:
            return
        if len(self.ind) != len(self.touch):
            return
        if self.force is None or self.z is None:
            return
        if len(self.z) != len(self.force) is None:
            return

        option1 = True
        # Option 1, use the original formula
        # E = 3*dFdd/8a ; dFdd = derivative of force vs delta
        if option1 is True:
            x = self.ind
            y = self.touch

            if(len(x)) < 1:  # check on length of ind
                return

            interp = self._ui.es_interpolate.isChecked()
            if interp is True:
                yi = interp1d(x, y)
                max_x = np.max(x)
                min_x = 1

                if np.min(x) > 1:
                    min_x = np.min(x)

                xx = np.arange(min_x, max_x, 1.0)
                yy = yi(xx)
                ddt = 1.0
            else:
                xx = x[1:]
                yy = y[1:]
                ddt = (x[-1]-x[1])/(len(x)-2)

            area = np.pi * xx * self.R
            contactradius = np.sqrt(xx * self.R)
            coeff = 3 * np.sqrt(np.pi) / 8 / np.sqrt(area)
            win = int(self._ui.es_win.value())
            if win % 2 == 0:
                win += 1
            if len(yy) <= win:
                return None, None
            order = int(self._ui.es_order.value())
            deriv = savgol_filter(yy, win, order, delta=ddt, deriv=1)
            Ey = coeff * deriv
            dwin = int(win - 1)
            Ex = contactradius[dwin:-dwin]
            Ey = Ey[dwin:-dwin]

            self.Ex = np.array(Ex)
            self.Ey = np.array(Ey)

        else:
            # Option2 use the prime function
            # E = 3*S/(1-S/k)/8a, S = dfFz, a = sqrt(R delta)
            # Note that this option is currently not in use as noise
            # in the curves causes singularity in the term S/(1-S/K) when S/K -> 1

            x = self.z
            y = self.force

            interp = self._ui.es_interpolate.isChecked()
            if interp is True:
                yi = interp1d(x, y)
                xx = np.linspace(min(x), max(x), len(x))
                yy = yi(xx)
                dz = xx[1]-xx[0]
                jcp = np.argmin(xx ** 2)
                yy_contact = yy[jcp:]
                xx_contact = xx[jcp:]
                ind = xx_contact - yy_contact/self.k
                ddt = dz
            else:
                xx = x[1:]
                yy = y[1:]
                ind = self.ind
                jcp = np.argmin(xx ** 2)
                ddt = np.average(xx[1:] - xx[:-1])

            win = int(self._ui.es_win.value())
            if win % 2 == 0:
                win += 1
            if len(yy) <= win:
                return None, None
            order = int(self._ui.es_order.value())
            dfdz = savgol_filter(yy, win, order, delta=ddt, deriv=1)
            S = dfdz[jcp:]  # need to remove zeros
            # sorted ind indexes, reduntant as interp already does it
            odg = np.argsort(ind)
            ind = ind[odg]
            nonull = ind > 0
            S = S[odg]
            S = S[nonull]
            ind = ind[nonull]
            Ex = np.sqrt(self.R * ind)
            Ey = 3*S/(1-S/self.k)/8/Ex
            dwin = int(win)
            Ex = Ex[dwin:-dwin]
            Ey = Ey[dwin:-dwin]

            self.Ex = np.array(Ex)
            self.Ey = np.array(Ey)

    def set_indentation(self):
        if self._ui.analysis.isChecked() is False:
            return
        if self.k is None:
            return
        if self. active is False:
            return
        z = self.z
        f = self.force
        iContact = np.argmin((z ** 2))

        Yf = f[iContact:]
        Xf = z[iContact:]
        self.ind = Xf - Yf / self.k
        self.touch = Yf

        self.set_elasticityspectra()  # calling set_elasticityspectra()

    def reset_E(self):
        self._E = None

    def reset_contactpoint(self):
        self._contactpoint = [0, 0]
        self._E = None

    def rewind_data(self):
        self._ind = None
        self._touch = None
        self._z = self._z_raw
        self._f = self._f_raw
        self._E = None
        self._Ex = None
        self._Ey = None

    def reset_data(self):
        self._z = None
        self._f = None
        self._ind = None
        self._touch = None
        self._E = None

    def set_XY(self, x, y):
        self.reset_data()
        self.reset_contactpoint()
        self._included = True
        self._active = True
        self.z_raw = x
        self.f_raw = y
        self._E = None

    def filter_all(self, recalculate_cp=True):
        self.rewind_data()
        if self._ui.prominency.isChecked() is True:
            pro = float(self._ui.prominency_prominency.value()) / 100.0
            winperc = int(self._ui.prominency_band.value())
            threshold = int(self._ui.prominency_minfreq.value())
            self.filter_prominence(pro, winperc, threshold)
        if self._filter is not None:
            self._f = self._filter(self)
        if self._filter is False:  # filter returns a False value
            self.active = False
            return
        if recalculate_cp is True:
            self.calculate_contactpoint()
        self.set_indentation()
        self.update_view()

    def filter_prominence(self, pro=0.2, winperc=1, threshold=25):
        if self.included is False:
            return
        # threshold is the minimum frequency to be eventually filtered
        # winperc is the width around the filtered frequency in % of the position
        # pro is the peak prominency
        y = self._f
        ff = np.fft.rfft(y, norm=None)
        idex = find_peaks(np.log(np.abs(ff)), prominence=pro)
        xgood = np.ones(len(ff.real)) > 0.5
        for imax in idex[0]:
            jwin = int(imax * winperc / 100)
            if imax > threshold and jwin == 0:
                xgood[imax] = False
            elif imax > threshold:
                ext1 = np.max([imax - jwin, 0])
                ext2 = np.min([imax + jwin + 1, len(xgood) - 1])
                for ii in range(ext1, ext2):
                    xgood[ii] = False
        if np.sum(xgood) < 50:
            return
        xf = np.arange(0, len(ff.real))
        yinterpreal = interp1d(xf[xgood], ff.real[xgood], kind='linear')
        yinterpimag = interp1d(xf[xgood], ff.imag[xgood], kind='linear')
        ff.real = yinterpreal(xf)
        ff.imag = yinterpimag(xf)
        self._f = np.fft.irfft(ff, n=len(y))

    def calculate_contactpoint(self):
        self.reset_contactpoint()
        if self.included is False:
            return
        if self.z is None or self.force is None or (len(self.z) != len(self.force)):
            return
        self._state = ST_BLK

        res = self._cpfunction(self)
        if res is None or res is False:
            self.active = False
            return
        # res[1] = 0.0  # sets force to zero at CP
        self._contactpoint = res
        self.set_indentation()
        self.update_view()

    def getFitted(self):
        if self._ui.analysis.isChecked() is False:
            return

        upto = np.min(
            [float(self._ui.fit_indentation.value()), np.max(self.ind)])
        x = np.linspace(0, upto, int(upto))
        y = hertz(x, self.E/1e9, self.R)

        x = x + y/self.k

        return x, y

    def fitHertz(self):
        if self._ui.analysis.isChecked() is False:
            return
        if self.ind is None or self.touch is None or (len(self.ind) != len(self.touch)):
            return
        seeds = [1000.0 / 1e9]
        try:
            R = self.R

            def Hertz(x, E):
                x = np.abs(x)
                poisson = 0.5
                # Eeff = E*1.0e9 #to convert E in GPa to keep consistency with the units nm and nN
                return (4.0 / 3.0) * (E / (1 - poisson ** 2)) * np.sqrt(R * x ** 3)

            indmax = float(self._ui.fit_indentation.value())
            jj = np.argmin((self.ind-indmax)**2)
            if jj < 5:
                return
            popt, pcov = curve_fit(
                Hertz, self.ind[:jj], self.touch[:jj], p0=seeds, maxfev=100000)
            # E_std = np.sqrt(pcov[0][0])
            self._E = popt[0]*1e9
        except (RuntimeError, ValueError):
            return

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
            if self._state < ST_BLK:
                return
            self._state = ST_BLU
        else:
            if self._state == ST_BLK:
                return
            self._state = ST_BLK
            self._tree.setCheckState(0, QtCore.Qt.Checked)
        self.update_view()

    @ property
    def included(self):
        return self._state > ST_RED

    @ included.setter
    def included(self, x):
        if x is False:
            if self._state == ST_RED:
                return
            else:
                self._state = ST_RED
                self._tree.setCheckState(0, QtCore.Qt.Unchecked)
        else:
            if self._state > ST_RED:
                return
            self._state = ST_BLK
            self._tree.setCheckState(0, QtCore.Qt.Checked)
        self.update_view()

    @ property
    def E(self):
        if self._E is None:
            self.fitHertz()
        return self._E

    @ E.setter
    def E(self, x):
        if self._E == x:
            return
        self._E = x
        self.update_view()

    @ property
    def x_contact_point(self):
        if self._contactpoint is None:
            return None
        return self._contactpoint[0]

    @ x_contact_point.setter
    def x_contact_point(self, x):
        if self._contactpoint[0] == x:
            return
        self._contactpoint[0] = x
        self.set_indentation()

    @ property
    def y_contact_point(self):
        if self._contactpoint is None:
            return None
        return self._contactpoint[1]

    @ y_contact_point.setter
    def y_contact_point(self, x):
        if self._contactpoint[1] == x:
            return
        self._contactpoint[1] = x
        self.set_indentation()

    @ property
    def z_raw(self):
        if self._z_raw is None:
            return None
        return self._z_raw - self.x_contact_point

    @ z_raw.setter
    def z_raw(self, x):
        if x is not None:
            x = np.array(x)
        self._z_raw = x
        self.z = x

    @ property
    def f_raw(self):
        if self._f_raw is None:
            return None
        return self._f_raw - self.y_contact_point

    @ f_raw.setter
    def f_raw(self, x):
        if x is not None:
            x = np.array(x)
        self._f_raw = x
        self.force = x

    @ property
    def z(self):
        if self._z is None or self.x_contact_point is None:
            return None
        delta = self._z - self.x_contact_point
        return delta

    @ z.setter
    def z(self, x):
        if sames(self._z, x) is False:
            if x is None:
                self._z = None
            else:
                x = np.array(x)
            self._z = x
            self.filter_all()

    @ property
    def force(self):
        if self._f is None or self.y_contact_point is None:
            return None
        return self._f - self.y_contact_point

    @ force.setter
    def force(self, x):
        if sames(self._f, x) is False:
            if x is not None:
                x = np.array(x)
            self._f = x
            self.update_view()
            self.filter_all()

    @ property
    def Ex(self):
        return self._ex

    @ Ex.setter
    def Ex(self, x):
        if sames(self._ex, x) is False:
            if x is not None:
                x = np.array(x)
            self._ex = x
            self.update_view()

    @ property
    def Ey(self):
        return self._ey

    @ Ey.setter
    def Ey(self, x):
        if sames(self._ey, x) is False:
            if x is not None:
                x = np.array(x)
            self._ey = x
            self.update_view()

    @ property
    def ind(self):
        return self._ind

    @ ind.setter
    def ind(self, x):
        if sames(self._ind, x) is False:
            if x is not None:
                x = np.array(x)
            self._ind = x
            self.update_view()

    @ property
    def touch(self):
        return self._touch

    @ touch.setter
    def touch(self, x):
        if sames(self._touch, x) is False:
            if x is not None:
                x = np.array(x)
            self._touch = x
            self.update_view()


def getMedCurve(xar, yar, loose=True, threshold=3, error=False):
    if loose is False:
        xmin = -np.inf
        xmax = np.inf
        deltax = 0
        nonecount = 0
        for x in xar:
            if x is not None and np.min(x) is not None:
                xmin = np.max([xmin, np.min(x)])
                xmax = np.min([xmax, np.max(x)])
                deltax += ((np.max(x)-np.min(x))/(len(x)-1))
            else:
                nonecount += 1
        deltax /= (len(xar)-nonecount)
        xnew = np.linspace(xmin, xmax, int((xmax-xmin)/(deltax)))
        ynew = np.zeros(len(xnew))
        for i in range(len(xar)):
            if xar[i] is not None and np.min(xar[i]) is not None:
                ycur = np.interp(xnew, xar[i], yar[i])
                ynew += ycur
        ynew /= (len(xar)-nonecount)
    else:
        xmin = np.inf
        xmax = -np.inf
        deltax = 0
        for x in xar:
            try:
                xmin = np.min([xmin, np.min(x)])
                xmax = np.max([xmax, np.max(x)])
                deltax += ((np.max(x) - np.min(x)) / (len(x) - 1))
            except TypeError:
                return
        deltax /= len(xar)
        xnewall = np.linspace(xmin, xmax, int((xmax - xmin) / deltax))
        ynewall = np.zeros(len(xnewall))
        count = np.zeros(len(xnewall))
        ys = np.zeros([len(xnewall), len(xar)])
        for i in range(len(xar)):
            imin = np.argmin((xnewall - np.min(xar[i])) ** 2)  # +1
            imax = np.argmin((xnewall - np.max(xar[i])) ** 2)  # -1
            ycur = np.interp(xnewall[imin:imax], xar[i], yar[i])
            ynewall[imin:imax] += ycur
            count[imin:imax] += 1
            for j in range(imin, imax):
                ys[j][i] = ycur[j-imin]
        cc = count >= threshold
        xnew = xnewall[cc]
        ynew = ynewall[cc] / count[cc]
        yerrs_new = ys[cc]
        yerr = []
        for j in range(len(yerrs_new)):
            squr_sum = 0
            num = 0
            std = 0
            for i in range(0, len(yerrs_new[j])):
                if yerrs_new[j][i] != 0:
                    squr_sum += (yerrs_new[j][i] - ynew[j]) ** 2
                    num += 1
            if num > 0:
                std = np.sqrt(squr_sum / num)
            yerr.append(std)
        yerr = np.asarray(yerr)
    if error == False:
        return xnew[:-1], ynew[:-1]
    elif error == True:
        return xnew[:-1], ynew[:-1], yerr[:-1]


LAMBD = 1.74


def TheExp(a, E0, Eb, d0):
    weight = np.exp(-LAMBD * a / d0)
    return Eb + (E0 - Eb) * weight


def fitExpSimple(a, y, sigma=None):
    seeds = [10000*1e-9, 1000*1e-9, 200]
    a = np.asarray(a)
    try:
        if sigma is None or any(sigma) == 0:
            popt1, pcov1 = curve_fit(
                TheExp, a[:-1], y[:-1], p0=seeds, maxfev=10000)
        else:
            popt1, pcov1 = curve_fit(
                TheExp, a[:-1], y[:-1], sigma=sigma[:-1], p0=seeds, maxfev=10000)  # sigma=sigma[:-1],
        stds1 = [np.sqrt(pcov1[0][0]), np.sqrt(
            pcov1[1][1]), np.sqrt(pcov1[2][2])]
        return popt1, stds1
    except:
        print('Exp fit failed!')
        return None
