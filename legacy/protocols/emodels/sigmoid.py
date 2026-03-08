#import the main panels structure, required
from ..panels import fitPanel
#import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from scipy.optimize import curve_fit
from magicgui.widgets import SpinBox

#Set here the details of the procedure
NAME = 'Sigmoid' #Name, please keep it short as it will appear in the combo box of the user interface
DESCRIPTION = 'Fit with a generic sigmoidal (logistic) function' #Free text
DOI = '' #set a DOI of a publication you want/suggest to be cited, empty if no reference
PARAMETERS = {'EH [Pa]':"Higher modulus",'EL [Pa]':"Lower modulus",'T [nm]':"Thickness", 'k [Pa/nm]': 'Sharpness'}

# Create your filter class by extending the main one
# Additional methods can be created, if required
class EModel(fitPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface 
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        # Parameters can be used as seeds or proper parameters (e.g. indentation depth ?) 
        #self.addParameter('maxind','float','Max indentation [nm]',800)
        self.addParameter('Smooth',SpinBox(value=100, name='Smooth', label='Upper Percentile threshold',min=60,max=100))
        self.addParameter('Lower',SpinBox(value=10, name='Lower', label='Lower Percentile threshold',min=5,max=50) )

    def theory(self,x,*parameters):
        EH,EL,T,k = parameters
        A = EH-EL
        return EL + A/(1+(np.exp(-4*(x-T)/k)))
        # sigmoid curve; use 4 so that k is the width of the transition

    def calculate(self, x,y):
        try:
            popt, pcov = curve_fit(self.theory, x, y, p0=[1000,200000,1e-6,1e-6], maxfev=10000)
        except RuntimeError:
            return False
        for p in popt:
            if p<0: 
                return False
        return popt
