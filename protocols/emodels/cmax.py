#import the main panels structure, required
from ..panels import fitPanel
#import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from magicgui.widgets import SpinBox

#Set here the details of the procedure
NAME = 'LineMax' #Name, please keep it short as it will appear in the combo box of the user interface
DESCRIPTION = 'Evaluate the average over a range and the maximum' #Free text
DOI = '' #set a DOI of a publication you want/suggest to be cited, empty if no reference
PARAMETERS = {'E [Pa]':"Average modulus",'M<E> [Pa]':"Median modulus",'Emax [Pa]':"Max modulus"}

# Create your filter class by extending the main one
# Additional methods can be created, if required
class EModel(fitPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface 
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        # Parameters can be used as seeds or proper parameters (e.g. indentation depth ?) 
        #self.addParameter('maxind','float','Max indentation [nm]',800)
        self.addParameter('Smooth',SpinBox(value=100, name='Smooth', label='Percentile threshold',min=60,max=100))

    def theory(self,x,*parameters):
        return parameters[0]*np.ones(len(x))

    def calculate(self, x,y):
        full = self.curve._E
        # This function gets the current x and y and returns the parameters.
        percentile = self.getValue('Smooth')
        if percentile < 100:
            threshold = np.percentile(full,percentile)
            maxi = np.average(full[full>threshold])
        else:
            maxi = np.max(full)
        return [np.average(y),np.median(full),maxi]
