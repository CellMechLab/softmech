#import the main panels structure, required
from ..panels import boxPanel
#import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from scipy.signal import savgol_filter

#Set here the details of the procedure
NAME = 'Second derivative' #Name, please keep it short as it will appear in the combo box of the user interface
DESCRIPTION = '' #Free text
DOI = '' #set a DOI of a publication you want/suggest to be cited, empty if no reference

# Create your filter class by extending the main one
# Additional methods can be created, if required
class CP(boxPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface 
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        self.addParameter('window','float','Window [nm]',20.0)
        self.addParameter('x range','float','X Range [nm]',1000.0)
        self.addParameter('f threshold','float','Safe threshold [nN]',10.0)

    def calculate(self, x, y):
        zz_x, ddf = self.getWeight(x,y)
        ddf_best_ind = np.argmin(ddf)
        jdd = np.argmin((x - zz_x[ddf_best_ind])**2)
        return [x[jdd], y[jdd]]

    def getRange(self, x, y):
        try:
            jmax = np.argmin((y - self.getValue('f threshold')*1e-9) ** 2)
            jmin = np.argmin((x - (x[jmax] - self.getValue('x range')*1e-9)) ** 2)
        except ValueError:
            return False
        return jmin, jmax

    def getWeight(self, x, y):
        jmin, jmax = self.getRange(x,y)
        if jmin is False:
            return False
        win = self.getValue('window')*1e-9
        xstep = (max(x)-min(x))/(len(x)-1)
        win = int(win/xstep)
        if win % 2 == 0:
            win += 1
        fsecond = savgol_filter(y, polyorder=4, deriv=2, window_length=win)
        return x[jmin:jmax], fsecond[jmin:jmax]
