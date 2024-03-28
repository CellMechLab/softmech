#import the main panels structure, required
from ..panels import fitPanel
#import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from scipy.optimize import curve_fit
from magicgui.widgets import  FloatSlider


#Set here the details of the procedure
NAME = 'Hertz Effective' #Name, please keep it short as it will appear in the combo box of the user interface
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
       pass

    def theory(self,x,elastic):
      if self.curve.tip['geometry']=='sphere':
          R = self.curve.tip['radius']
          return (4.0 / 3.0) * (elastic) * np.sqrt(R * x ** 3)
      elif self.curve.tip['geometry']=='pyramid':
          ang = self.curve.tip['angle'] #see DOI for definition
          return 0.7453 * ((elastic*np.tan(ang*np.pi/180.0))) * x**2
      elif self.curve.tip['geometry']=='cylinder':
          R = self.curve.tip['radius']
          return (2.0/1.0) * (elastic) * (R * x)
      elif self.curve.tip['geometry']=='cone':
          ang = self.curve.tip['angle'] 
          return (2.0/1.0) * ((elastic*np.tan(ang*np.pi/180.0)) / (np.pi)) * x**2
      else:
          raise Exception('No data for the tip defined')

    def calculate(self, x,y):
        # This function gets the current x and y and returns the parameters.
        try:
            popt, pcov = curve_fit(self.theory, x, y, p0=[1000], maxfev=1000)
        except RuntimeError:
            return False
        return popt
