# import the main panels structure, required
from ..panels import boxPanel
# import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from scipy.optimize import curve_fit
from magicgui.widgets import  FloatSpinBox,SpinBox
from scipy.signal import savgol_filter


# Set here the details of the procedure
# Name, please keep it short as it will appear in the combo box of the user interface
NAME = 'Offset removal'
# Free text
DESCRIPTION = 'Removes offset obtained from baseline of F-z curves. Baseline is identified through thresholding (Threshold method of contact point). Ideal for data whose baseline trend hinders correct calculation of the contact point'
DOI = ''  # set a DOI of a publication you want/suggest to be cited, empty if no reference

# Create your filter class by extending the main one
# Additional methods can be created, if required


class Filter(boxPanel):
    def create(self):
        self.addParameter('percentile',SpinBox(value=50, name='percentile', label='Baseline percent [%]',min=1,max=99))

    def calculate(self, x,y):
        x_base, y_base = self.get_baseline(x,y)
        return x, y-np.average(y_base)

    def get_baseline(self, x,y):
        perc = self.getValue('percentile')
        k = int(perc*len(x)/100)
        return x[:k],y[:k]
    