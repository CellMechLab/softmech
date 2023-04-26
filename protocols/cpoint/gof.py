from ..panels import boxPanel
from scipy.optimize import curve_fit
from magicgui.widgets import  FloatSpinBox,SpinBox

from scipy.stats import linregress

NAME = 'GoF simple'
DESCRIPTION = 'Computes CP based on the simplified GoF method using the Hertz solution for a spherical indenter'
DOI = ''

import numpy as np

class CP(boxPanel): 
    def create(self):
        self.addParameter('fitwindow', FloatSpinBox(value=200.0, name='fit window', label='Fit window [nm]'))
        self.addParameter('minx', SpinBox(value=50, name='minx', label='Min x %',min=1,max=99))
        self.addParameter('maxf', SpinBox(value=50, name='maxf', label='Max force %',min=1,max=99))

    def get_indentation(self, z, f, iContact, win):
        # Retunrs indentation f and ind from f and z
        Zf = z[iContact: iContact + win] - z[iContact]
        force = f[iContact: iContact + win] - f[iContact]
        delta = Zf - force / self.curve.spring_constant
        return delta, force
    
    def getFit(self,delta,force):
        linforce = (force**2)**(1/3)
        analysis = linregress(delta,linforce)
        return (analysis.rvalue)**2
    
    def calculate(self, x, y):
        # Retunrs contact point (z0, f0) based on max R**2
        dx = (np.max(x)-np.min(x))/(len(x)-1)
        window = int(float(self.getValue('fitwindow')*1e-9)/dx)
        fthreshold = np.min(y) + (np.max(y)-np.min(y))*self.getValue('maxf')/100
        xthreshold = np.min(x) + (np.max(x)-np.min(x))*self.getValue('minx')/100
        jmax = np.argmin((y-fthreshold)**2)
        jmin = np.argmin((x-xthreshold)**2)
        
        R2 = []
        for j in range(jmin,jmax):
            d,f = self.get_indentation(x, y, j, window)
            try:
                R2.append(self.getFit(d,f))
            except:
                R2.append(0)
        r_best_ind = np.argmax(R2)
        j_gof = jmin + r_best_ind
        return [x[j_gof], y[j_gof]]

