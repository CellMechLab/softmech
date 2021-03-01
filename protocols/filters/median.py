# import the main panels structure, required
from ..panels import boxPanel
# import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from scipy.signal import medfilt

# Set here the details of the procedure
# Name, please keep it short as it will appear in the combo box of the user interface
NAME = 'Median'
DESCRIPTION = 'Apply a median filter to the input array using a local window-size given by kernel_size. The array will automatically be zero-padded.'  # Free text
# set a DOI of a publication you want/suggest to be cited, empty if no reference
DOI = 'https://doi.org/10.1038/s41592-019-0686-2'

# Create your filter class by extending the main one
# Additional methods can be created, if required


class Filter(boxPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        self.addParameter('win', 'float', 'Window size [nm]', 25)

    def calculate(self, x, y, curve=None):
        win = self.getValue('win')*1e-9
        xstep = (max(x) - min(x)) / (len(x) - 1)
        win = int(win / xstep)
        if win % 2 == 0:
            win += 1
        xfiltered = x
        yfiltered = medfilt(y, win)
        return xfiltered, yfiltered
