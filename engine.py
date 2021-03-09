import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

dataset = []

def dataformat(box,n):
    indicators=[]
    for i in range(n):
        n1 = np.average(box[i])
        n2 = np.std(box[i])
        if n2 > n1:
            pippo = '{0:.4g}&plusmn;{1:.4g}'.format(n1,n2)
        else:
            p = int(np.floor(np.log10(n2)))
            if np.abs(p)<2:
                er = int(n2/10**p)*10**p
                val = int( n1/10**p )*10**p
                pippo = '{}&plusmn;{}'.format(val,er)
            else:
                er = int(n2/10**p)
                val = int( n1/10**p )
                pippo = '({}&plusmn;{})10<sup>{}<sup>'.format(val,er,p)
        indicators.append( pippo )
    return indicators

def reorganise(stack,n):
    box = []
    data = np.array(stack)
    for i in range(n):
        box.append( data[:,i] )
    return box

class curve(object):
    def __init__(self,structure=None):
        self.data = {'F': None,'Z':None}
        self.spring_constant = 1.0
        self.tip = {'geometry':None}
        self._cp=[]
        self.reset()
        if structure is not None:
            self.load(structure)

    def load(self,structure):
        for k,v in structure.items():
            setattr(self,k,v)
        self.reset()

    def setZF(self,ret):
        if ret is None or ret is False:
            return
        x,y = ret
        self._Z,self._F = np.array(x),np.array(y)

    def getJclose(self,x0,x):
        x = np.array(x)
        return np.argmin( (x-x0)**2 )

    def getFizi(self,xmin,xmax):
        jmin = self.getJclose(xmin,self._Zi)
        jmax = self.getJclose(xmax,self._Zi)
        return np.array(self._Zi[jmin:jmax]),np.array(self._Fi[jmin:jmax])

    def getEze(self,xmin,xmax):
        jmin = self.getJclose(xmin,self._Ze)
        jmax = self.getJclose(xmax,self._Ze)
        return np.array(self._Ze[jmin:jmax]),np.array(self._E[jmin:jmax])

    def resetCP(self):
        self._cp = None
        self._Fi = None
        self._Zi = None
        self._E = None
        self._Ze = None
        self._Fparams = None
        self._Eparams = None

    def reset(self):
        self._F = np.array(self.data['F'])
        self._Z = np.array(self.data['Z'])
        self._cp = None
        self._Fi = None
        self._Zi = None
        self._E = None
        self._Ze = None
        self._Fparams = None
        self._Eparams = None

    def calc_indentation(self, setzeroforce = True):
        iContact = np.argmin( (self._Z - self._cp[0] )** 2)
        if setzeroforce is True:
            Yf = self._F[iContact:]-self._cp[1]
        else:
            Yf = self._F[iContact:]
        Xf = self._Z[iContact:]-self._cp[0]
        self._Zi = Xf - Yf / self.spring_constant
        self._Fi = Yf

    def calc_elspectra(self,win,order,interp=True):
        x = self._Zi
        y = self._Fi
        if(len(x)) < 1:  # check on length of ind
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

        self._Ze = np.array(Ex)
        self._E = np.array(Ey)