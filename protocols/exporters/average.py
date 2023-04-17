#import the main panels structure, required
from ..panels import boxPanel
#import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from magicgui.widgets import  RadioButtons,CheckBox

#Set here the details of the procedure
NAME = 'Average curve' #Name, please keep it short as it will appear in the combo box of the user interface
DESCRIPTION = 'Plot (and save) average curve' #Free text
DOI = '' #set a DOI of a publication you want/suggest to be cited, empty if no reference

def averageall(xall,yall,direction):
    
    N = np.max( [ len(x) for x in xall] )

    if direction == 'H':
        dset = yall
        ddep = xall
    else:
        dset = xall
        ddep = yall
    
    sup = np.min( [ np.max(d) for d in dset if d is not None] )
    inf = np.max( [ np.min(d) for d in dset if d is not None] )
    newax = np.linspace(inf,sup,N)
    neway = []
    for x,y in zip(dset,ddep):
        neway.append(np.interp(newax, x, y))
    newyavg = np.average(np.array(neway),axis=0)
    
    if direction == 'H':
        return  newyavg,newax
    else:
        return newax,newyavg

# Create your filter class by extending the main one
# Additional methods can be created, if required
class EXP(boxPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface 
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        #self.addParameter('ZeroRange',FloatSpinBox(value=500.0, name='ZeroRange', label='Range to set the zero [nN]',min=20,max=9999))
        w1 = RadioButtons(choices=['Indentation','Elastography'], label='Dataset:', value='Indentation')        
        w2 = RadioButtons(choices=['H','V'], label='Direction:', value='H')
        w3 = CheckBox(text='Preview', value=False)
        self.addParameter('Dataset',w1)
        self.addParameter('Direction',w2)
        self.addParameter('Preview',w3)
        
    def export(self, filename, exp):
        data =exp.getData()
        wone = self.getValue('Dataset')
        xall=[]
        yall=[]
        for c in data:
            if wone == 'Indentation':
                if c._Zi is not None:
                    xall.append(c._Zi)
                    yall.append(c._Fi)
            else:
                if c._Ze is not None:
                    xall.append(c._Ze)
                    yall.append(c._E)

        if len(xall)==0:
            return
                    
        x,y = averageall(xall,yall,self.getValue('Direction'))
        
        if self.getValue('Preview') is True:
            import matplotlib.pyplot as plt
            for xx,yy in zip(xall,yall):
                plt.plot(xx,yy,'r-',alpha=0.25)    
            plt.plot(x,y,'b-')
            plt.show()

        if wone == 'Indentation':
            header = '#SoftMech export data\n#Average F-d curve\n'
        else:
            header = '#SoftMech export data\n#Average E-d curve\n'
        
        f = open(filename,'w')
        header+='#\n#DATA\n'
        f.write(header)
        for line in range(len(x)):
            f.write('{}\t{}\n'.format(x[line],y[line]))
        f.close()

        return