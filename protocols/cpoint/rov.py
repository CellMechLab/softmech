from ..panels import magicPanel
from magicgui.widgets import  FloatSlider
import numpy as np

NAME = 'RoV'
DESCRIPTION = 'Identify the CP by ratio of variances'
DOI = ''

import numpy as np

class CP(magicPanel): 
    def create(self):
        self.addParameter('Fthreshold', FloatSlider(value=10.0, name='Fthreshold', label='Safe Threshold [nN]'))
        self.addParameter('Xrange',FloatSlider(value=1000.0, name='Fthreshold', label='XRange',min=0))
        self.addParameter('windowr',FloatSlider(value=200.0, name='Fthreshold', label='Window RoV [nm]',min=0))

    def calculate(self, x, y):
        zz_x, rov = self.getWeight(x,y) 
        rov_best_ind = np.argmax(rov)
        j_rov = np.argmin((x-zz_x[rov_best_ind])**2)
        return [x[j_rov], y[j_rov]]

    def getRange(self, x, y):
        try:
            jmax = np.argmin((y - self.getValue('Fthreshold')*1e-9) ** 2)
            jmin = np.argmin((x - (x[jmax] - self.getValue('Xrange')*1e-9)) ** 2)
        except ValueError:
            return False
        return jmin, jmax

    def getWeight(self, x, y):
        jmin, jmax = self.getRange(x, y)
        winr = self.getValue('windowr')*1e-9
        xstep = (max(x)-min(x))/(len(x)-1)
        win = int(winr/xstep)
        if (len(y) - jmax) < int(win):
            return False
        if (jmin) < int(win):
            return False
        rov = []
        for j in range(jmin, jmax):
            rov.append((np.var(y[j+1: j+win])) / (np.var(y[j-win: j-1])))
        return x[jmin:jmax], rov

    