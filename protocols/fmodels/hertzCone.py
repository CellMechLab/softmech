#import the main panels structure, required
from ..panels import fitPanel
#import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from scipy.optimize import curve_fit
import math

#Set here the details of the procedure
NAME = 'Hertz Cone' #Name, please keep it short as it will appear in the combo box of the user interface
DESCRIPTION = 'Fit indentation data with the Hertz model - Conical indenter' #Free text
DOI = '10.1115/1.2720924' #set a DOI of a publication you want/suggest to be cited, empty if no reference
PARAMETERS = {'E [Pa]':"Young's modulus"}

# Create your filter class by extending the main one
# Additional methods can be created, if required
class FModel(fitPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface 
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        self.addParameter('poisson','float','Poisson ratio',0.5)

    def theory(self,x,*parameters):
        if self.curve.tip['geometry']=='cone':
            ang = self.curve.tip['angle'] #see DOI for definition
        else:
            return False
        # Calculate the fitting function for a specific set of parameters
        return (2.0/1.0) * ((parameters[0]*math.tan(ang*math.pi/180.0)) / (math.pi*(1-self.getValue('poisson') ** 2))) * x**2

    def calculate(self, x,y):
        # This function gets the current x and y and returns the parameters.
        try:
            popt, pcov = curve_fit(self.theory, x, y, p0=[1000], maxfev=1000)
        except RuntimeError:
            return False
        return popt

