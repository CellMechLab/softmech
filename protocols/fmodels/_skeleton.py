#import the main panels structure, required
from ..panels import boxPanel
#import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from scipy.optimize import curve_fit


#Set here the details of the procedure
NAME = 'Fitting procedure' #Name, please keep it short as it will appear in the combo box of the user interface
DESCRIPTION = 'Fit indentation data with ...' #Free text
DOI = '' #set a DOI of a publication you want/suggest to be cited, empty if no reference
PARAMETERS = {} #set a dictionary with the fitting model parameters. For example,
#for a simple hertz model this would be PARAMETERS = {'E [Pa]':"Young's modulus"}

# Create your filter class by extending the main one
# Additional methods can be created, if required
class FModel(boxPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface 
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        # Parameters can be used as seeds or proper parameters (e.g. indentation depth ?) 
        self.addParameter('para1','int','Integer parameter [a.u.]',0)
        self.addParameter('para2','float','Float parameter [N]',25)
        self.addParameter('para3','combo',"Select smooth method",'med',
            dataset = {'med':'MedFilt','sg':'Savitzky-Golay'}) #Possible values are passed as dictionary; values are the labels

    def theory(self,x,*parameters):
        # Calculate the fitting function for a specific set of parameters
        return x**2

    def calculate(self, x,y):
        # This function gets the current x and y and returns the parameters.
        p1 = self.getValue('para1') # get the value of the parameters as set by the user
        if p1 > 10:
            return False # If an error occurs, return False
        pars = [1,1]
        return pars
