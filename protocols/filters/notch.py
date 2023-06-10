# import the main panels structure, required
from ..panels import boxPanel
# import here your procedure-specific modules, no requirements (numpy as an example)
from scipy import signal
import numpy as np
from magicgui.widgets import  FloatSpinBox, SpinBox


# Set here the details of the procedure
NAME = 'Notch'  # Name, please keep it short as it will appear in the combo box of the user interface
DESCRIPTION = 'Apply a notch filter to eliminate oscillations'  # Free text
# set a DOI of a publication you want/suggest to be cited, empty if no reference
#DOI = 'https://doi.org/10.1038/s41592-019-0686-2'

# Create your filter class by extending the main one
# Additional methods can be created, if required


class Filter(boxPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        self.addParameter('time',FloatSpinBox(value=100.0, name='time', label='Period [nm]',min=1))
        self.addParameter('quality',SpinBox(value=10, name='quality', label='Quality factor [nm]',min=1,max=1000000))

    def calculate(self, x, y, curve=None):
        dz = np.abs(x[-1]-x[0])/(len(x)-1)
        freq = dz/(self.getValue('time')*1e-9)
        Q = self.getValue('quality')
        b,a = signal.iirnotch(freq,Q)
        y_smooth = signal.filtfilt(b,a,y)
        return x, y_smooth
