from ..panels import boxPanel
import numpy as np

NAME = 'RoV 1st'
DESCRIPTION = 'Identify the CP by ratio of variances'
DOI = ''

import numpy as np

class CP(boxPanel): # Ratio of variances First peak
    def create(self):
        self.addParameter('Fthreshold','float','Safe Threshold [nN]',10.0)
        self.addParameter('Xrange','float','X Range [nm]',1000.0)
        self.addParameter('windowr','int','Window RoV [nm]',200)

    def getRange(self, c):
        x = c._z
        y = c._f
        try:
            jmax = np.argmin((y - self.getValue('Fthreshold')) ** 2)
            jmin = np.argmin((x - (x[jmax] - self.getValue('Xrange'))) ** 2)
        except ValueError:
            return False
        return jmin, jmax

    def getWeight(self, c):
        jmin, jmax = self.getRange(c)
        winr = self.getValue('windowr')
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

    def calculate(self, z,f,curve=None):
        zz_x, rov = self.getWeight(curve) #da correggere
        rov_best_ind = np.argmax(rov)
        j_rov = np.argmin((z-zz_x[rov_best_ind])**2)
        return [z[j_rov], f[j_rov]]