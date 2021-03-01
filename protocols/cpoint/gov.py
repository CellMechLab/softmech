from ..panels import boxPanel
from scipy.optimize import curve_fit

NAME = 'Goodness of Fit'
DESCRIPTION = 'Identify the CP by thresholding it'
DOI = ''

import numpy as np

class CP(boxPanel): # Goodness of Fit (GoF)
    def create(self):
        pass
        #self.windowr = CPPFloat('Window Fit [nm]')
        #self.windowr.setValue(200.0)
        #self.Xrange = CPPFloat('X Range [nm]')
        #self.Xrange.setValue(1000.0)
        #self.Fthreshold = CPPFloat('Safe Threshold [nN]')
        #self.Fthreshold.setValue(10.0)
        #self.addParameter(self.windowr)
        #self.addParameter(self.Xrange)
        #self.addParameter(self.Fthreshold)

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
    def calculate(self, z,f,curve=None):
        try:
            zz_x, R_squared = self.getWeight(curve)
        except TypeError:
            return False
        R_best_ind = np.argmax(R_squared)
        j_GoF = np.argmin((z-zz_x[R_best_ind])**2)
        return [z[j_GoF], f[j_GoF]]