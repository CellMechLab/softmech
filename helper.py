def doPlot(cC):
        panels = 1 + (1 if cC._Zi is not None else 0) + (1 if cC._Ze is not None else 0)
        import matplotlib.pyplot as plt
        i=1
        plt.subplot(1,panels,1)
        plt.plot(cC._Z,cC._F,'k.')
        plt.title('Curve F(Z)')
        if cC._Zi is not None:
            i+=1
            plt.subplot(1,panels,i)
            plt.title('Curve F(ind)')
            plt.plot(cC._Zi,cC._Fi,'k.')
            if cC._Fparams is not None:                
                x,y = cC.getFizi(self.ui.zi_min.value()*1e-9,self.ui.zi_max.value()*1e-9)
                plt.plot(x,self._fmodel.getTheory(x,cC._Fparams,curve=cC),'r--')
        if cC._Ze is not None:
            i+=1
            plt.subplot(1,panels,i)
            plt.title('Curve E(ind)')
            plt.plot(cC._Ze,cC._E,'k.')
            if cC._Eparams is not None:
                x,y = cC.getEze(self.ui.ze_min.value()*1e-9,self.ui.ze_max.value()*1e-9)
                plt.plot(x,self._emodel.getTheory(x,cC._Eparams,curve=cC),'r--')