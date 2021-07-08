#import the main panels structure, required
from ..panels import fitPanel
#import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from scipy.optimize import curve_fit

#Set here the details of the procedure
NAME = 'Hertz Sphere' #Name, please keep it short as it will appear in the combo box of the user interface
DESCRIPTION = 'Fit indentation data with the Hertz model - Spherical indenter' #Free text
DOI = '' #set a DOI of a publication you want/suggest to be cited, empty if no reference
PARAMETERS = {'E [Pa]':"Young's modulus"}

# Create your filter class by extending the main one
# Additional methods can be created, if required
class FModel(fitPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface 
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        # Parameters can be used as seeds or proper parameters (e.g. indentation depth ?) 
        self.addParameter('poisson','float','Poisson ratio',0.5)

    def theory(self,x,*parameters):
        if self.curve.tip['geometry']=='sphere':
            R = self.curve.tip['radius']
        else:
            return False
        # Calculate the fitting function for a specific set of parameters
        return (4.0 / 3.0) * (parameters[0] / (1 - self.getValue('poisson') ** 2)) * np.sqrt(R * x ** 3)

    def calculate(self, x,y):
        # This function gets the current x and y and returns the parameters.
        try:
            popt, pcov = curve_fit(self.theory, x, y, p0=[1000], maxfev=1000)
        except RuntimeError:
            return False
        return popt
