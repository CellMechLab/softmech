from ..panels import boxPanel
import numpy as np
from magicgui.widgets import  FloatSpinBox


NAME = 'Threshold'
DESCRIPTION = 'Identify the CP by thresholding it'
DOI = ''

import numpy as np

class CP(boxPanel):  # Threshold
    def create(self):
        self.addParameter('Athreshold',FloatSpinBox(value=10.0, name='Athreshold', label='Align Threshold [nN]',min=0))
        self.addParameter('deltaX',FloatSpinBox(value=2000.0, name='deltaX', label='Align left step [nm]',min=0,max=10000))
        self.addParameter('Fthreshold',FloatSpinBox(value=100.0, name='Fthreshold', label='AVG area [nm]',min=0))
        self.addParameter('shift',FloatSpinBox(value=0.0, name='shift', label='shift CP [nm]',min=0))

    def calculate(self, x,y):
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
        sh = self.getValue('shift')*1e-9
        xcp = x[jcp] + sh
        ycp = y[np.argmin( (x-xcp)**2)]
        return [xcp, ycp]
