#import the main panels structure, required
from ..panels import boxPanel
#import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from magicgui.widgets import  RadioButtons

#Set here the details of the procedure
NAME = 'Scatter data' #Name, please keep it short as it will appear in the combo box of the user interface
DESCRIPTION = 'Save scatter data analysis' #Free text
DOI = '' #set a DOI of a publication you want/suggest to be cited, empty if no reference

# Create your filter class by extending the main one
# Additional methods can be created, if required
class EXP(boxPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface 
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        #self.addParameter('ZeroRange',FloatSpinBox(value=500.0, name='ZeroRange', label='Range to set the zero [nN]',min=20,max=9999))
        choices = ['Indentation','Elastography']
        w2 = RadioButtons(choices=choices, label='Dataset:', value='Indentation')
        self.addParameter('Dataset',w2)
    
    def export(self, filename, exp):

        wone = self.getValue('Dataset')
        if wone == 'Indentation':
            if exp.fdata is None or exp.fdata is False or len(exp.fdata) == 0:
                return
            header = '#SoftMech export data\n#Indentation analysis\n#\n#FModel parameters\n'
            model = exp._fmodel
            data = exp.fdata
        else:
            if exp.edata is None or exp.edata is False or len(exp.edata) == 0:
                return
            header = '#SoftMech export data\n#Elastography analysis\n#\n#EModel parameters\n'
            model = exp._emodel
            data = exp.edata
        
        f = open(filename,'w')

        for key in model.fitparameters:
            header += '#{}:{}\n'.format(key,model.fitparameters[key])
        header+='#\n#'
        pre = ''
        for key in model.fitparameters:
            header = header + pre + key
            pre = ','
        header+='\n#\n#DATA\n'
        f.write(header)
        for line in range(len(data[0])):
            pre = ''
            for column in range(len(data)):
                f.write(pre + str(data[column][line]))
                pre=','
            f.write('\n')
        f.close()

        return