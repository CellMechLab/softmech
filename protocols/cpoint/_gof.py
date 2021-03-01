import numpy as np
from ..panels import boxPanel
from scipy.optimize import curve_fit

# TO EDIT FOLLOWING CONTACT MECHANICS MODELS IMPLEMENTATION #

NAME = 'Goodness of Fit'
DESCRIPTION = 'This is the most standard strategy when using successive search\
procedures and has been used in the majority of cell mechanics studies reported so far.\
For each trial point, F-z data are first converted to F-δ\
assuming that δi = 0 and Fi = 0 at the location of the trial point i.\
Then, the appropriate contact-mechanics model is fitted to the contact part of the F-δ data,\
and the r2 value of the fit is used as the test parameter. Contact point is then established as\
the trial point which yields the highest value for r**2'
DOI = '10.1038/srep21267'


class CP(boxPanel): 
    def create(self):
        self.addParameter('fit window', 'float', 'Fit window [m]', 200.0e-9)
        self.addParameter('x range', 'float', 'X range [m]', 1000.0e-9)
        self.addParameter('force tresh', 'float', 'Force Threshold[m]', 10.0e-9)

    def calculate(self, x, y, curve=None):
        # Retunrs contact point based on max R**2 following Hertz fit
        try:
            zz_x, R_squared = self.getWeight(x, y)
        except TypeError:
            return False
        R_best_ind = np.argmax(R_squared)
        j_GoF = np.argmin((x-zz_x[R_best_ind])**2)
        return [x[j_GoF], y[j_GoF]]

    def getRange(self, x, y):
        # Returns min and max indices of F-z data
        try:
            jmax = np.argmin((y - self.getValue('force tresh')) ** 2)
            jmin = np.argmin((x - (x[jmax] - self.getValue('x range'))) ** 2)
        except ValueError:
            return False
        return jmin, jmax

    def getWeight(self, x, y):
        # Retunrs weight array (r**2) and corresponding index array.
        # Uses get_indentation and fit methods defined below
        jmin, jmax = self.getRange(x, y)
        if jmin is False or jmax is False:
            return False
        zwin = self.getValue('fit window')
        zstep = (max(x) - min(x)) / (len(x) - 1)
        win = int(zwin / zstep)

        R_squared = []
        interval = np.arange(jmin, jmax)
        for j in interval:
            try:
                ind, Yf = self.get_indentation(x, y, j, win)
                E_std = self.fit(x, y, ind, Yf)
                R_squared.append(E_std)
            except TypeError:
                return False
        return y[jmin:jmax], R_squared

    # Retunrs indentation (ind) and f from z vs f data
    def get_indentation(self, x, y, iContact, win):
        R = 3e-6  # to change
        if (iContact + win) > len(x):
            return False
        Zf = x[iContact: iContact + win] - x[iContact]
        Yf = y[iContact: iContact + win] - y[iContact]
        ind = Zf - Yf / 5  # k to change
        # Fit only for small indentations
        ind = ind[ind <= 0.1*R]
        Yf = Yf[ind <= 0.1*R]
        return ind, Yf

    def fit(self, x, y, ind, f):
        seeds = [1000.0 / 1e9]
        try:
            R = 3e-6  # to change

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
