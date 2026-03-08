from ..panels import boxPanel
from scipy.optimize import curve_fit
from magicgui.widgets import  FloatSpinBox


NAME = 'GoF sphere'
DESCRIPTION = 'Computes CP based on the GoF method using the Hertz solution for a spherical indenter'
DOI = ''

import numpy as np

class CP(boxPanel): 
    def create(self):
        self.addParameter('fit window', FloatSpinBox(value=200.0, name='fit window', label='Fit window [nm]'))
        self.addParameter('x range', FloatSpinBox(value=1000.0, name='x range', label='X Range [nm]'))
        self.addParameter('force threshold', FloatSpinBox(value=10.0, name='force threshold', label='Force threshold [nN]'))

    def calculate(self, x, y):
        # Retunrs contact point (z0, f0) based on max R**2
        try:
            zz_x, r_squared = self.getWeight(x,y)
        except TypeError:
            return False
        r_best_ind = np.argmax(r_squared)
        j_gof = np.argmin((x-zz_x[r_best_ind])**2)
        return [x[j_gof], y[j_gof]]

    # Returns min and max indices of f-z data considered
    def getRange(self, x, y):
        try:
            jmax = np.argmin((y - self.getValue('force threshold')*1e-9) ** 2)
            jmin = np.argmin((x - (x[jmax] - self.getValue('x range')*1e-9)) ** 2)
        except ValueError:
            return False
        return jmin, jmax

    def getWeight(self, x, y):
        # Retunrs weight array (R**2) and corresponding index array. Uses get_indentation and fit methods defined below
        out = self.getRange(x, y)
        if out is False:
            return False
        jmin, jmax = out
        zwin = self.getValue('fit window') * 1e-9
        zstep = (max(x) - min(x)) / (len(x) - 1)
        win = int(zwin / zstep)
        if (len(y) - jmax) < win:
            jmax = len(y)-1-win
        if jmax<=jmin:
            return False

        r_squared = []
        j_x = np.arange(jmin, jmax)
        for j in j_x:
            try:
                ind, Yf = self.get_indentation(x, y, j, win)
                E_std = self.fit(x, y, ind, Yf)
                r_squared.append(E_std)
            except TypeError:
                return False
        return x[jmin:jmax], r_squared

    def get_indentation(self, x, y, iContact, win):
        # Retunrs indentation f and ind from f and z
        z = x
        f = y
        R = self.curve.tip['radius']
        if (iContact + win) > len(z):
            return False
        Zf = z[iContact: iContact + win] - z[iContact]
        Yf = f[iContact: iContact + win] - f[iContact]
        ind = Zf - Yf / self.curve.spring_constant
        Yf = Yf[ind <= 0.1*R]   # fit only for small indentations
        ind = ind[ind <= 0.1*R]        
        return ind, Yf

    def fit(self, x, y, ind, f):
        seeds = [1000.0 / 1e9]
        try:
            R = self.curve.tip['radius']
            def Hertz(x, E):
                x = np.abs(x)
                poisson = 0.5
                return (4.0 / 3.0) * (E / (1 - poisson ** 2)) * np.sqrt(R * x ** 3)
            popt, pcov = curve_fit(Hertz, ind, f, p0=seeds, maxfev=100000)
            residuals = f - Hertz(ind, *popt)
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((f-np.mean(f))**2)
            R_squared = 1 - (ss_res / ss_tot)
            return R_squared
        except (RuntimeError, ValueError):
            return False

    