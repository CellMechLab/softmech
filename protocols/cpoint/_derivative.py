from ..panels import boxPanel

NAME = 'Second derivative'
DESCRIPTION = 'Identify the CP by second der'
DOI = ''

import numpy as np

class CP(boxPanel): # Second Derivative
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
