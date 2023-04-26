# import the main panels structure, required
from ..panels import boxPanel
# import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from scipy.optimize import curve_fit
from magicgui.widgets import  SpinBox
from scipy.signal import savgol_filter


# Set here the details of the procedure
# Name, please keep it short as it will appear in the combo box of the user interface
NAME = 'Polynomial Detrend'
# Free text
DESCRIPTION = 'Removes polynomial baseline till where most of the points are'
DOI = ''  # set a DOI of a publication you want/suggest to be cited, empty if no reference

# Create your filter class by extending the main one
# Additional methods can be created, if required


class Filter(boxPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        self.addParameter('percentile',SpinBox(value=90, name='percentile', label='Baseline percentile [%]',min=1,max=99))
        self.addParameter('degree',SpinBox(value=2, name='degree', label='Polynomial degree',min=2,max=6))


    def calculate(self, x,y):
        perc = self.getValue('percentile')
        deg = self.getValue('degree')

        threshold = np.percentile(y,perc)
        iLast = len(x)-1
        if y[-1]<threshold:
            iLast = len(y)-1
        else:
            for i in range(iLast-1,0,-1):
                if y[i] > threshold and y[i-1]<=threshold:
                    iLast = i
                    break
        xfit = x[:iLast]
        yfit = y[:iLast]

        pol = np.polyfit(xfit,yfit,deg)

        return x, y-np.polyval(pol,x)