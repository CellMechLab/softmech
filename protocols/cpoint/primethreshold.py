#import the main panels structure, required
from ..panels import boxPanel
#import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d

#Set here the details of the procedure
NAME = 'Prime function threshold' #Name, please keep it short as it will appear in the combo box of the user interface
DESCRIPTION = '' #Free text
DOI = '' #set a DOI of a publication you want/suggest to be cited, empty if no reference

# Create your filter class by extending the main one
# Additional methods can be created, if required
class CP(boxPanel):
    def create(self):
        # This function is required and describes the form to be created in the user interface 
        # The last value is the initial value of the field; currently 3 types are supported: int, float and combo
        self.addParameter('Athreshold','float','Align Threshold [nN/nm]', 0.0005)
        self.addParameter('deltaX','float','Align left step [nm]',2000.0)
        self.addParameter('Fthreshold','float','AVG area [nm]',100.0)
        self.addParameter('shift','float','shift CP [nm]', 0)


    def calculate(self, x, y, curve = None):  
        # calculates CP baed on prime function threshold
        primeth = self.getValue('Athreshold')
        z_false, prime = self.getWeight(x,y)
        xstep = (max(x)-min(x))/(len(x)-1)
        win = 31*1e-9
        win = int(win/xstep)
        fi = interp1d(x, y)
        z = np.linspace(min(x), max(x), len(x))
        f = fi(z)
        z = z[win:-win]
        f = f[win:-win]
        if primeth > np.max(prime) or primeth < np.min(prime):
            return False
        jrov = 0
        for j in range(len(prime)-1, 1, -1):
            if prime[j] > primeth and prime[j-1] < primeth:
                jrov = j
                break
        x0 = z[jrov]
        dx = self.getValue('deltaX')*1e-9
        ddx = self.getValue('Fthreshold')*1e-9
        if ddx <= 0:
            jxalign = np.argmin((z - (x0 - dx)) ** 2)
            dS0 = prime[jxalign]
        else:
            jxalignLeft = np.argmin((z-(x0-dx-ddx))**2)
            jxalignRight = np.argmin((z-(x0-dx+ddx))**2)
            dS0 = np.average(prime[jxalignLeft:jxalignRight])
        jcp = jrov
        for j in range(jrov, 1, -1):
            if prime[j] > dS0 and prime[j-1] < dS0:
                jcp = j
                break
        return [z[jcp], f[jcp]]

    def getWeight(self, x, y): 
        # Weight is the prime function
        z = x
        f = y
        try:
            win = 31*1e-9  # arbitrary (insert as input parameter?)
            xstep = (max(x)-min(x))/(len(x)-1)
            win = int(win/xstep)
            order = 4  # arbitrary (insert as input parameter?)
            fi = interp1d(z, f)
            zz = np.linspace(min(z), max(z), len(z))
            ff = fi(zz)
            dz = z[1]-z[0]
            dfdz = savgol_filter(ff, win, order, delta=dz,
                                 deriv=1)
            S = dfdz / (1-dfdz)  # c.k in denominator makes it unstable
        except:
            return False
        return z[win:-win], S[win:-win]
