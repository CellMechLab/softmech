from ..panels import boxPanel
import numpy as np
from magicgui.widgets import  FloatSpinBox,SpinBox


NAME = 'Threshold'
DESCRIPTION = 'Identify the CP by thresholding it'
DOI = ''

import numpy as np

class CP(boxPanel):  # Threshold
    def create(self):
        self.addParameter('startth', FloatSpinBox(value=2.0, name='startth', label='Starting threshold [nN]'))
        self.addParameter('minx', SpinBox(value=1, name='minx', label='Min x %',min=1,max=99))
        self.addParameter('maxx', SpinBox(value=60, name='maxx', label='Max x %',min=1,max=99))
        self.addParameter('offset', FloatSpinBox(value=0.0, name='offset', label='Force offset [pN]',min = -1000.0,max=1000.0))

    def calculate(self, x,y):
        yth = self.getValue('startth')*1e-9
        offset = self.getValue('offset')*1e-12
        if yth < np.min(y):
            return False
        if np.min(y)+offset >= yth:
            return False
        jstart = np.argmin((y-yth)**2)
        xmin = np.min(x) + (np.max(x)-np.min(x))*self.getValue('minx')/100
        xmax = np.min(x) + (np.max(x)-np.min(x))*self.getValue('maxx')/100
        imax = np.argmin((x-xmax)**2)
        imin = np.argmin((x-xmin)**2)
        baseline = np.average(y[imin:imax])
        jcp = 0
        for j in range(jstart,0,-1):
            if y[j]>baseline+offset and y[j-1]<=baseline+offset:
                jcp = j
                break
        xcp = x[jcp]
        ycp = y[jcp]
        return [xcp, ycp]
