#import the main panels structure, required
from ..panels import fitPanel
#import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from scipy.optimize import curve_fit
from magicgui.widgets import  FloatSlider

#Set here the details of the procedure
NAME = 'Bilayer' #Name, please keep it short as it will appear in the combo box of the user interface
DESCRIPTION = 'Bilayer model' #Free text
DOI = '' #set a DOI of a publication you want/suggest to be cited, empty if no reference
PARAMETERS = {'E0 [Pa]':"Cortex Young's modulus", 'Eb [Pa]':"Bulk Young's modulus", 'd [nm]':"Cortex thickness"}

# Create your filter class by extending the main one
# Additional methods can be created, if required
class EModel(fitPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface 
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        # Parameters can be used as seeds or proper parameters (e.g. indentation depth ?) 
        #self.addParameter('maxind','float','Max indentation [nm]',800)
        #self.addParameter('poisson','float','Poisson ratio',0.5)
        self.addParameter('Lambda',FloatSlider(value=1.74, name='Lambda', label='Lambda coefficient',min=1,max=2))

    def theory(self,x,*parameters):
        R = self.curve.tip['radius']
        d = parameters[2]*1e-9
        phi = np.exp( -self.getValue('Lambda')*np.sqrt(R*x)/d )
        return parameters[1]+(parameters[0]-parameters[1])*phi

    def calculate(self, x,y):
        # This function gets the current x and y and returns the parameters.
        try:
            popt, pcov = curve_fit(self.theory, x, y, p0=[100000,1000,1000], maxfev=10000)
        except RuntimeError:
            return False
        return popt
