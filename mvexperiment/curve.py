import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import medfilt
from scipy.signal import savgol_filter as savgol

MODE_DIRECTION_BACKWARD = 1
MODE_DIRECTION_FORWARD = 2
MODE_DIRECTIONS_PAUSE = 3
MODE_FEEDBACK_ON = 1
MODE_FEEDBACK_OFF = 2
MODE_TRIGGER_TIME = 1
MODE_TRIGGER_FORCE = 2
MODE_TRIGGER_POSITION = 3


def Gauss(x, x0, a0, s0):
    return a0 * np.exp(-((x - x0) / s0) ** 2)


def Decay(x, A, s):
    return A*np.exp(-(x/s))


def GGauss(x, x1, x2, a1, a2, s1, s2):
    return a1 * np.exp(-((x - x1) / s1) ** 2) + a2 * np.exp(-((x - x2) / s2) ** 2)


class Segment(object):
    def __init__(self, parent=None, z=None, f=None):
        self.z = z
        self.f = f
        self.active = True
        self.iContact = 0  # index of the contact point
        self.outContact = 0  # index of the last out-of-contact point
        self.parent = parent
        self.speed = None  # to be indicated in nm/s, for internal consinstency
        self.mode_direction = None  # see modes
        # indicates whether the feedback is active (for pause)
        self.mode_feedback = None
        self.mode_setpoint = None  # in case of feedback ON, the corresponding setpoint
        self.mode_trigger = None  # the trigger used to stop the segment
        self.mode_threshold = None  # the threshold of the above trigger
        self.poisson = 0.5
        self.young = None  # calculated Young's modulus based on Hertzian fit
        # Last point of the indentation used to make the Hertzian fit
        self.youngIThreshold = None
        self.indentation = None  # indentation
        # force corresponding to indentation, only to simplify plotting and managing
        self.touch = None
        self.H_indentation = None
        self.H_touch = None
        self.H_pressure = None
        self.elastography = None

        # To filter or smooth the curve, we use a fraction of the points of the curve, defined as follows
        # for the general smoothing (smoothCurve function)
        self._filterLength = 1 / 30
        # There should be at leat this fraction of the curve before the contact point
        self._contactLength = 1/20

    def hasBilayer(self):
        if self.elastography is not None and self.elastography.hasBilayer() is True:
            return True
        return False

    def setData(self, z, f, reorder=False):
        if reorder is True:
            newz = np.linspace(min(z), max(z), len(z))
            fint = np.interp(newz, z, f)
            z = newz
            f = fint
        self.z = z
        self.f = f

    def plot(self, mode='curve', label=None, color='b', alpha=1):
        if mode == 'curve':
            plt.xlabel('Displacement [nm]')
            if label is None:
                plt.plot(self.z, self.f, color=color, ls='-')
            else:
                plt.plot(self.z, self.f, color=color, ls='-', label=label)
            if self.outContact > 0:
                plt.plot(self.z[:self.outContact],
                         self.f[:self.outContact], 'y-')
            if self.iContact > 0:
                plt.plot([self.z[self.iContact]], [
                         self.f[self.iContact]], 'go')
            plt.ylabel('Force [nN]')
            plt.legend()
        elif mode == 'light':
            if self.iContact > 0:
                offsetX = self.z[self.iContact]
                offsetY = np.average(self.f[:self.iContact])
                plt.plot(self.z-offsetX, self.f-offsetY,
                         color=color, ls='-', alpha=alpha)
            else:
                plt.plot(self.z, self.f, color=color, ls='-', alpha=alpha)
        elif mode == 'indlight':
            if self.indentation is not None:
                plt.plot(self.indentation, self.touch,
                         color=color, ls='-', alpha=alpha)
        elif mode == 'indentation':
            plt.xlabel('Indentation [nm]')
            if self.indentation is not None:
                if label is None:
                    plt.plot(self.indentation, self.touch, color=color, ls='-')
                else:
                    plt.plot(self.indentation, self.touch,
                             color=color, ls='-', label=label)
                if self.young is not None:
                    if self.youngIThreshold is not None:
                        plt.plot(self.indentation[:self.youngIThreshold], self.hertz(
                            self.indentation[:self.youngIThreshold]), 'g-', label='Hertz fit E={}'.format(int(self.young*1e9)))
                    else:
                        plt.plot(self.indentation, self.hertz(
                            self.indentation), 'g-', label='Hertz fit E={}'.format(int(self.young*1e9)))
            plt.ylabel('Force [nN]')
            plt.legend()
        elif mode == 'elastography':
            if self.elastography is not None and self.elastography.Ex is not None:
                plt.xlabel('Indentation [nm]')
                if label is None:
                    plt.plot(self.elastography.Ex,
                             self.elastography.Ey, color=color, ls='-')
                else:
                    plt.plot(self.elastography.Ex, self.elastography.Ey,
                             color=color, ls='-', label=label)
                if self.elastography.bilData is not None:
                    ec, eb, t = self.elastography.bilData
                    lbl = 'Bilayer fit\nE_c={}\nE_b={}\bT={}'.format(
                        int(ec * 100)/100, int(eb*100)/100, int(t))
                    plt.plot(self.elastography.Ex, self.elastography.EBilayer(
                        self.elastography.Ex, ec, eb, t), 'g-', label=lbl)
                plt.ylabel('Young\'s modulus [Pa]')
                plt.legend()

    def getNodd(self, fraction, total=None):
        if total is None:
            total = len(self.z)
        N = int(total*fraction)
        if N % 2 == 0:
            N += 1
        return N

    def smooth(self, method='sg'):
        N = self.getNodd(self._filterLength)
        if method == 'sg':
            try:
                y = savgol(self.f, N, 6, 0)
                self.f = y
            except:
                method = 'basic'
        if method == 'basic':
            self.f = medfilt(self.f, N)

    def findOutOfContactRegion(self, weight=20.0, refine=False):
        yy, xx = np.histogram(self.f, bins='auto')
        xx = (xx[1:]+xx[:-1])/2.0
        try:
            func = Gauss
            out = curve_fit(Gauss, xx, yy, p0=[
                            xx[np.argmax(yy)], np.max(yy), 1.0])
            threshold = out[0][1] / weight
        except RuntimeError:
            try:
                func = Decay
                out = curve_fit(Decay, xx, yy, p0=[np.max(yy), 1.0])
                threshold = out[0][0]/weight
            except RuntimeError:
                return
        fit = func(xx, *out[0])
        if refine is True and len(out[0]) == 3:
            # try to refine
            x0, a0, s0 = out[0]
            try:
                out2 = curve_fit(GGauss, xx, yy, p0=[
                                 x0, x0+s0, a0, a0/5.0, s0, s0])
                threshold = out2[0][2]/weight
            except RuntimeError:
                pass
        jend = 0
        for i in range(len(xx) - 1, 0, -1):
            if fit[i] < threshold and fit[i - 1] > threshold:
                jend = i
                break
        xcontact = np.max(self.z[self.f < xx[jend]])
        self.outContact = np.argmin((self.z - xcontact) ** 2)

    def findContactPoint(self):
        if self.outContact == 0:
            return
        pcoe = np.polyfit(self.z[:self.outContact],
                          self.f[:self.outContact], 1)
        ypoly = np.polyval(pcoe, self.z)
        if self.f[self.outContact] < ypoly[self.outContact]:
            self.iContact = self.outContact
        else:
            for i in range(self.outContact, 0, -1):
                if self.f[i] < ypoly[i]:
                    self.iContact = i
                    break
        return True

    def createIndentation(self):
        if self.iContact == 0:
            return
        offsetY = np.average(self.f[:self.iContact])
        offsetX = self.z[self.iContact]
        Yf = self.f[self.iContact:]-offsetY
        Xf = self.z[self.iContact:]-offsetX
        self.indentation = Xf-Yf/self.parent.cantilever_k
        self.touch = Yf

    def hertz(self, x, E=None):  # NB E should be in nN/nm^2 = 10^9 N/m^2 -> internal units for E is GPa
        if E is None:
            E = self.young
        x = np.abs(x)
        # Eeff = E*1.0e9 #to convert E in GPa to keep consistency with the units nm and nN
        y = (4.0 / 3.0) * (E / (1 - self.poisson ** 2)) * \
            np.sqrt(self.parent.tip_radius * x ** 3)
        return y  # y will be in nN

    def fitHertz(self, seed=1000.0/1e9, threshold=None, thresholdType='indentation'):
        self.young = None
        if self.indentation is None:
            return
        x = self.indentation
        y = self.touch
        if threshold is not None:
            imax = len(x)
            if thresholdType == 'indentation':
                if threshold > np.max(x):
                    return False
                imax = np.argmin((x-threshold)**2)
            else:
                if threshold > np.max(y) or threshold < np.min(y):
                    return False
                imax = np.argmin((y - threshold) ** 2)
            if imax > 10:
                x = x[:imax]
                y = y[:imax]
                self.youngIThreshold = imax
            else:
                return False
        seeds = [seed]
        # NB the curve is forced to have F=0 at indentation 0
        try:
            popt, pcov = curve_fit(self.hertz, x, y, p0=seeds, maxfev=10000)
            self.young = popt[0]
            self.H_indentation = x
            self.H_touch = y
            area = np.pi * self.parent.tip_radius * x
            self.H_pressure = y / area
            return self.young*1e9

        except RuntimeError:
            return False
        return True
