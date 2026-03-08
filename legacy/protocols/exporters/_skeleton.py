#import the main panels structure, required
from ..panels import boxPanel
#import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np

from magicgui.widgets import  FloatSpinBox

#Set here the details of the procedure
NAME = 'Prominency' #Name, please keep it short as it will appear in the combo box of the user interface
DESCRIPTION = 'Filters prominent peaks in the Fourier space, to eliminate oscillations' #Free text
DOI = '' #set a DOI of a publication you want/suggest to be cited, empty if no reference

# Create your filter class by extending the main one
# Additional methods can be created, if required
class EXP(boxPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface 
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        self.addParameter('ZeroRange',FloatSpinBox(value=500.0, name='ZeroRange', label='Range to set the zero [nN]',min=20,max=9999))

    def calculate(self, x, y):
        # This function gets the current x and y and returns the filtered version.
        p1 = self.getValue('para1') # get the value of the parameters as set by the user
        if p1 > 10:
            return False # If an error occurs, return False
        xcp = x[0]
        ycp = y[0]
        return xcp,ycp
