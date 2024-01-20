#import the main panels structure, required
from ..panels import boxPanel
#import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from magicgui.widgets import  CheckBox,ComboBox,SpinBox

from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

#Set here the details of the procedure
NAME = 'Average curve' #Name, please keep it short as it will appear in the combo box of the user interface
DESCRIPTION = 'Plot (and save) average curve' #Free text
DOI = '' #set a DOI of a publication you want/suggest to be cited, empty if no reference

def averageall(xall,yall,direction,loose=100):
    
    N = np.max( [ len(x) for x in xall] )

    if direction == 'H':
        dset = yall
        ddep = xall
    else:
        dset = xall
        ddep = yall
        
    inf = np.max( [ np.min(d) for d in dset if d is not None] )
    if loose >= 100:
        sup = np.min( [ np.max(d) for d in dset if d is not None] )
    else:
        sups = [ np.max(d) for d in dset if d is not None]
        sup = np.percentile(sups,100-loose)
        
    newax = np.linspace(inf,sup,N)
    neway = []
    for x,y in zip(dset,ddep):
        if np.max(x)>= sup:
            neway.append(np.interp(newax, x, y))
    newyavg = np.average(np.array(neway),axis=0)
    newstd = np.std(np.array(neway),axis=0)
    
    if direction == 'H':
        return  newyavg,newax,newstd
    else:
        return newax,newyavg,newstd
    
def calc_elspectra(x,y,self,win,order,interp=True):
        if(len(x)) < 2:  # check on length of ind
            return None
        if interp is True:
            yi = interp1d(x, y)
            max_x = np.max(x)
            min_x = 1e-9
            if np.min(x) > 1e-9:
                min_x = np.min(x)
            xx = np.arange(min_x, max_x, 1.0e-9)
            yy = yi(xx)
            ddt = 1.0e-9
        else:
            xx = x[1:]
            yy = y[1:]
            ddt = (x[-1]-x[1])/(len(x)-2)
        
        if self.tip['geometry']=='sphere':
            R = self.tip['radius']
            area = np.pi * xx * R
            #contactradius = np.sqrt(xx * R)
            coeff = 3 * np.sqrt(np.pi) / 8 / np.sqrt(area)
        elif self.tip['geometry']=='cylinder':
            R = self.tip['radius']
            coeff = 3 / 8 / R
        elif self.tip['geometry']=='cone':
            aradius = 2*xx / np.tan(self.tip['angle']*np.pi/180.0)/np.pi
            coeff = 3  / 8 / aradius
        elif self.tip['geometry']=='pyramid': #Bilodeau formula
            aradius = 0.709*xx*np.tan(self.tip['angle']*np.pi/180.0)
            coeff = 3  / 8 / aradius
        else:
            return False
        if win % 2 == 0:
                win += 1
        if len(yy) <= win:
            return False   
        deriv = savgol_filter(yy, win, order, delta=ddt, deriv=1)
        Ey = coeff * deriv
        dwin = int(win - 1)
        Ex = xx[dwin:-dwin] #contactradius[dwin:-dwin]
        Ey = Ey[dwin:-dwin]

        return np.array(Ex),np.array(Ey)

# Create your filter class by extending the main one
# Additional methods can be created, if required
class EXP(boxPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface 
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        #self.addParameter('ZeroRange',FloatSpinBox(value=500.0, name='ZeroRange', label='Range to set the zero [nN]',min=20,max=9999))
        w1 = ComboBox(choices=['Force','Elasticity','El from F'], label='Dataset:', value='Force')        
        w2 = ComboBox(choices=['H','V'], label='Direction:', value='V')
        w3 = CheckBox(text='Preview', value=False)
        self.addParameter('Dataset',w1)
        self.addParameter('Direction',w2)
        self.addParameter('Loose',SpinBox(value=100,min=10,max=100,label="Looseness"))
        
    def calculate(self,exp):
        data =exp.getData()
        wone = self.getValue('Dataset')
        xall=[]
        yall=[]
        x2all=[]
        y2all=[]
        for c in data:
            if wone == 'Force':
                if c._Zi is not None:
                    xall.append(c._Zi)
                    yall.append(c._Fi)
            else:
                if c._Ze is not None:
                    xall.append(c._Ze)
                    yall.append(c._E)
                if wone == 'El from F':
                    if c._Zi is not None:
                        x2all.append(c._Zi)
                        y2all.append(c._Fi)

        if len(xall)==0:
            return
        std=None
        if wone == 'El from F':
            x2,y2,std = averageall(x2all,y2all,self.getValue('Direction'),self.getValue('Loose'))
            x,y = calc_elspectra(x2,y2,data[0],*exp.getEPars())
        else:
            x,y,std = averageall(xall,yall,self.getValue('Direction'),self.getValue('Loose'))
        
        return xall,yall,x,y,std

    def preview(self, ax, exp):
        xall,yall,x,y,std = self.calculate(exp)
        wone = self.getValue('Dataset')
        for xx,yy in zip(xall,yall):
            ax.set_xlabel('Indentation [nm]')                
            if wone == 'Force':
                ax.set_ylabel('Force [nN]')
                coe = 1e9
            else:
                ax.set_ylabel('Elasticity spectrum [kPa]')
                coe = 1/1000.0
            ax.plot(xx*1e9,yy*coe,'r-',alpha=0.25)    
        if wone == 'Force':
            coe =1e9
        else:
            coe = 1/1000.0
        ax.plot(x*1e9,y*coe,'b-',label='Average curve')
        return
        
    def export(self, filename, exp):
        xall,yall,x,y,std = self.calculate(exp)
        wone = self.getValue('Dataset')
        ds = exp.getData()
        if wone == 'Force':
            header = '#SoftMech export data\n#Average F-d curve\n'
        else:
            header = '#SoftMech export data\n#Average E-d curve\n'
        header+='#Direction:{}\n#Loose:{}\n'.format(self.getValue('Direction'),self.getValue('Loose'))
        geometry = ds[0].tip['geometry']
        header+='#Tip shape: {}\n'.format(geometry)
        if geometry in ['sphere','cylinder']:
            header+='#Tip radius: {}\n'.format(ds[0].tip['radius'])
        else:
            header+='#Tip angle: {}\n'.format(ds[0].tip['angle'])
        header+='#Elastic constant: {}\n'.format(ds[0].spring_constant)
        if wone == 'Force':
            if self.getValue('Direction')=='V':
                header+='#Columns: Indentation <F> SigmaF\n'
            else:
                header+='#Columns: <Indentation> F SigmaZ\n'
        else:
            if self.getValue('Direction')=='V':
                header+='#Columns: Indentation <E>\n'
            else:
                header+='#Columns: <Indentation> E\n'
        f = open(filename,'w')
        header+='#\n#DATA\n'
        f.write(header)
        for line in range(len(x)):
            if wone == 'Force':
                f.write('{}\t{}\t{}\n'.format(x[line],y[line],std[line]))
            else:
                f.write('{}\t{}\n'.format(x[line],y[line]))
        f.close()
        return