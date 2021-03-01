from ..panels import boxPanel
import numpy as np

NAME = 'RoV 1st'
DESCRIPTION = 'Identify the CP by ratio of variances. On the non-contact part of\
the indentation curve, there is no mechanical interaction between the probe and the sample.\
 As the cantilever moves towards the sample, no changes in the cantilever deflection are\
 measured, apart from those arising from instrumentation noise. If we were to measure the\
variance of the deflection signal in a small interval on the non-contact region of the curve,\
 it will be small. Once the tip of the cantilever proceeds to indent the sample’s surface,\
the increasing force applied by the probe onto the sample’s surface is recorded as a slowly\
 increasing deflection of the cantilever. Therefore, the variance of the deflection signal\
 computed on a small interval within the contact region of the curve will we much larger than\
 that computed in the non-contact region. Importantly, the variances measured in two different\
 intervals belonging both to the non-contact region will be equal, and likewise, the variances\
 measured in two different intervals of the contact region will be similar. To take advantage\
 of these phenomena, the test parameter RoV is defined as the ratio of the variances of the\
 deflection signal, computed in two small windows to each side of the trial point. For trial\
 points well within the non-contact region of the curve, RoV will be close to 1 whereas\
 for trial points well-within the contact region, RoV will be slightly larger than 1. \
Notably, RoV will display a peak in the vicinity of the CP which will be readily detected\
 using the successive search procedure'
DOI = '10.1038/srep21267'


class CP(boxPanel):  
    def create(self):
        self.addParameter('Fthreshold', 'float', 'Force Threshold [nN]', 10.0)
        self.addParameter('Xrange', 'float', 'X Range [nm]', 1000.0)
        self.addParameter('windowr', 'int', 'Window RoV [nm]', 200)

    def calculate(self, x, y, curve=None):
        zz_x, rov = self.getWeight(x,y)  
        rov_best_ind = np.argmax(rov)
        j_rov = np.argmin((x-zz_x[rov_best_ind])**2)
        return [x[j_rov], y[j_rov]]

    def getRange(self, x, y):
        try:
            jmax = np.argmin((y - self.getValue('Fthreshold')*1e-9) ** 2)
            jmin = np.argmin((x - (x[jmax] - self.getValue('Xrange')*1e-9)) ** 2)
        except ValueError:
            return False
        return jmin, jmax

    def getWeight(self, x, y):
        jmin, jmax = self.getRange(x,y)
        winr = self.getValue('windowr')*1e-9
        if (len(y) - jmax) < int(winr/2):
            return False
        if (jmin) < int(winr/2):
            return False
        rov = []
        for j in range(jmin, jmax):
            rov.append((np.var(y[j+1:j+winr])) / (np.var(y[j-winr:j-1])))
        return x[jmin:jmax], rov

