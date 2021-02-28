from ..panels import boxPanel
import numpy as np

NAME = 'Threshold'
DESCRIPTION = 'Identify the CP by thresholding it'
DOI = ''

import numpy as np

class CP(boxPanel):  # Threshold
    def create(self):
        self.addParameter('Athreshold','float','Align Threshold [nN]',10.0)
        self.addParameter('deltaX','float','Align left step [nm]',2000.0)
        self.addParameter('Fthreshold','float','AVG area [nm]',100.0)

    def calculate(self, x,y,curve=None):
        yth = self.getValue('Athreshold')*1e-9
        if yth > np.max(y) or yth < np.min(y):
            return False
        jrov = 0
        for j in range(len(y)-1, 1, -1):
            if y[j] > yth and y[j-1] < yth:
                jrov = j
                break
        if jrov==0 or jrov==len(y)-1:
            return False
        x0 = x[jrov]
        dx = self.getValue('deltaX')*1e-9
        ddx = self.getValue('Fthreshold')*1e-9
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
        if jcp == 0:
            return False
        return [x[jcp], y[jcp]]
