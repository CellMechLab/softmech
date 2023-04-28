from ..panels import boxPanel
import numpy as np
from magicgui.widgets import  FloatSpinBox


NAME = 'AutoThreshold'
DESCRIPTION = 'Identify the CP by thresholding it over different degrees'
DOI = ''

import numpy as np
from scipy.signal import savgol_filter,argrelmin

class CP(boxPanel):  # Threshold
    def create(self):
        self.addParameter('ZeroRange',FloatSpinBox(value=500.0, name='ZeroRange', label='Range to set the zero [nm]',min=1,max=9999))
    def calculate(self, x,y):
        
        deg = 0 #self.getValue('Degree')
        worky = np.copy(y)
        #window = self.getValue('Window')
        #if window%2 == 0:
        #    window+=1            
        #if deg > 0:
        #    for k in range(deg):
        #        worky = savgol_filter(worky,window,3,deriv=1)
        
        xtarget = np.min(x) + self.getValue('ZeroRange')*1e-9
        jtarget = np.argmin( np.abs(x-xtarget) )
        
        #which direction?
        if x[0]<x[-1]:
            xlin = x[:jtarget]
            ylin = worky[:jtarget]
            m,q = np.polyfit(xlin,ylin,1)
        else:
            xlin = x[jtarget:]
            ylin = worky[jtarget:]
            m,q = np.polyfit(xlin,ylin,1)
        
        worky = worky-m*x-q
        
        differences = (worky[1:]+worky[:-1])/2
        midpoints = np.array(list(set(differences)))
        midpoints.sort()
        
        crossings = []
        for threshold in midpoints[midpoints>0]:
            crossings.append( np.sum( np.bitwise_and( (worky[1:]>threshold),(worky[:-1]<threshold) )))
        crossings=np.array(crossings)
        
        candidates = np.where(crossings==1)
        if len(candidates)==0 or len(candidates[0])==0:
            return False
        elif len(midpoints[midpoints>0])==0:
            return False
        else:
            inflection = midpoints[midpoints>0][candidates[0][0]]
            jcpguess = np.argmin( np.abs(differences-inflection) )+1
        
        xcp = x[jcpguess]
        ycp = y[jcpguess]
        return [xcp, ycp]
