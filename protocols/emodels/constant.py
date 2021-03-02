#import the main panels structure, required
from ..panels import boxPanel
#import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np

#Set here the details of the procedure
NAME = 'Constant' #Name, please keep it short as it will appear in the combo box of the user interface
DESCRIPTION = 'Evaluate the average value' #Free text
DOI = '' #set a DOI of a publication you want/suggest to be cited, empty if no reference

# Create your filter class by extending the main one
# Additional methods can be created, if required
class EModel(boxPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface 
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        # Parameters can be used as seeds or proper parameters (e.g. indentation depth ?) 
        #self.addParameter('maxind','float','Max indentation [nm]',800)
        #self.addParameter('poisson','float','Poisson ratio',0.5)
        pass

    def theory(self,x,*parameters):
        return parameters[0]*np.ones(len(x))

    def calculate(self, x,y):
        # This function gets the current x and y and returns the parameters.
        return [np.average(y)]
