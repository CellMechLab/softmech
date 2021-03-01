# import the main panels structure, required
from ..panels import boxPanel
# import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from scipy.optimize import curve_fit


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
        self.addParameter('Athreshold', 'float',
                          'Align Threshold [nN]', 10.0)
        self.addParameter('deltaX', 'float', 'Align left step [nm]', 2000.0)
        self.addParameter('Fthreshold', 'float', 'AVG area [nm]', 100.0)

    def calculate(self, x, y, curve=None):
        # This function gets the current x and y and returns the filtered version.
        # get the value of the parameters as set by the user

        # Conversion to array important when using physical units
        x = np.array(x)
        y = np.array(y)
        # Getting baseline
        yth = self.getValue('Athreshold')*1e-9
        if yth > np.max(y) or yth < np.min(y):
            return False
        jrov = 0
        for j in range(len(y)-1, 1, -1):
            if y[j] > yth and y[j-1] < yth:
                jrov = j
                break
        x0 = x[jrov]
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
        if jcp > 2:
            x_base = x[:jcp]
            y_base = y[:jcp]
        else:
            return False

        # Fitting baseline
        def lin_fit(x, a, b):
            return a*x + b
        popt, pcov = curve_fit(lin_fit, x_base, y_base, maxfev=10000)
        x_lin = np.linspace(min(x), max(x), len(x))
        y_trendline = lin_fit(x_lin, *popt)  # Calculated over whole z range

        # Detrending
        xfiltered = x
        yfiltered = y-y_trendline
        return xfiltered, yfiltered
