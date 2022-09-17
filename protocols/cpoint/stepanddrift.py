from ..panels import boxPanel
import numpy as np
from magicgui.widgets import  FloatSpinBox,SpinBox
from scipy.signal import savgol_filter

NAME = 'Step'
DESCRIPTION = 'Identify the CP by steps in first derivative'
DOI = ''

import numpy as np

class CP(boxPanel):  # Threshold
    def create(self):
        self.addParameter('threshold',FloatSpinBox(value=10.0, name='threshold', label='Align Threshold [pN]',min=0))
        self.addParameter('thratio',FloatSpinBox(value=25, name='thratio', label='Threshold ratio [pN]',min=0,max = 100))
        self.addParameter('window',SpinBox(value=101, name='window', label='Smoothing window [points]',min=11,max=9999,step=2))

    def calculate(self, x,y):
        dy = savgol_filter(y,self.getValue('window'),3,deriv=1)            
        for j in range(len(dy)):
            if dy[j]>self.getValue('threshold')/1e12:
                break
        for k in range(j,0,-1):
            if dy[k]<self.getValue('thratio')*self.getValue('threshold')/1e14:
                break
        return [x[k], y[k]]

        