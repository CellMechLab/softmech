#import the main panels structure, required
from ..panels import boxPanel
#import here your procedure-specific modules, no requirements (numpy as an example)
import numpy as np
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d

#Set here the details of the procedure
NAME = 'Prime Function' #Name, please keep it short as it will appear in the combo box of the user interface
DESCRIPTION = 'Identify the CP by the prime function' #Free text
DOI = '' #set a DOI of a publication you want/suggest to be cited, empty if no reference

# Create your filter class by extending the main one
# Additional methods can be created, if required
class CP(boxPanel):
    def create(self):
        self.addParameter('Athreshold','float','Align Threshold [nN/nm]',0.0005)
        self.addParameter('deltaX','float','Align left step [nm]',2000.0)
        self.addParameter('Fthreshold','float','AVG area [nm]',100.0)

    def calculate(self, x, y, curve=None): 
        primeth = self.getValue('Athreshold')
        z_false, prime = self.getWeight(x,y)
        fi = interp1d(x, y)
        z = np.linspace(min(x), max(x), len(x))
        f = fi(x)
        win = 31
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
        dx = self.getValue('deltaX')
        ddx = self.getValue('Fthreshold')
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
        # weight is the prime function
        try:
            win = 31  # arbitrary (insert as input parameter?)
            order = 4  # arbitrary (insert as input parameter?)
            fi = interp1d(x, y)
            z = np.linspace(min(x), max(x), len(x))
            f = fi(z)
            dz = x[1]-x[0]
            dfdz = savgol_filter(f, win, order, delta=dz,
                                 deriv=1)
            S = dfdz / (1-dfdz)  # c.k in denominator makes it unstable
        except:
            return False
        return x[win:-win], S[win:-win]


