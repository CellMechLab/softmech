#import the main panels structure, required
from ..panels import boxPanel
#import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np

#Set here the details of the procedure
NAME = 'Threshold' #Name, please keep it short as it will appear in the combo box of the user interface
DESCRIPTION = 'Screen the curves based on the max value achieved by the indentation' #Free text
DOI = '' #set a DOI of a publication you want/suggest to be cited, empty if no reference

# Create your filter class by extending the main one
# Additional methods can be created, if required
class Screen(boxPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface 
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        self.addParameter('Threshold','float','Force Threshold [nN]',1.0)

    def calculate(self, x, y):
        # This function gets the current x and y and returns the filtered version.
        th = self.getValue('Threshold')*1e-9
        if np.max(y) < th:
            return False
        return True