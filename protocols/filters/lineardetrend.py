# import the main panels structure, required
from ..panels import boxPanel
# import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from scipy.optimize import curve_fit
from magicgui.widgets import  FloatSpinBox,SpinBox
from scipy.signal import savgol_filter


# Set here the details of the procedure
# Name, please keep it short as it will appear in the combo box of the user interface
NAME = 'Linear Detrend'
# Free text
DESCRIPTION = 'Removes linear trend obtained from baseline of F-z curves. Baseline is identified through thresholding (Threshold method of contact point). Ideal for data whose baseline trend hinders correct calculation of the contact point'
DOI = ''  # set a DOI of a publication you want/suggest to be cited, empty if no reference

# Create your filter class by extending the main one
# Additional methods can be created, if required


class Filter(boxPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        self.addParameter('threshold',FloatSpinBox(value=10.0, name='threshold', label='Align Threshold [pN]',min=0))
        self.addParameter('window',SpinBox(value=101, name='window', label='Smoothing window [points]',min=11,max=9999,step=2))


    def calculate(self, x,y):
        x_base, y_base = self.get_baseline(x,y)
        m,q = np.polyfit(x_base,y_base,1)
        return x, y-m*x-q

    def get_baseline(self, x,y):
        dy = savgol_filter(y,self.getValue('window'),3,deriv=1)            
        for j in range(len(dy)):
            if dy[j]>self.getValue('threshold')/1e12:
                break
        k=j
        for k in range(j,0,-1):
            if dy[k]<0:
                break
        return [x[:k], y[:k]]
