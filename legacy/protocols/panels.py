from PySide6 import QtGui, QtWidgets, QtCore
from importlib import import_module
from magicgui.widgets import Label
            
class boxPanel:  # Contact point class
    def __init__(self):
        self._parameters = {}
        self.create()

    def create(self):
        #This function contains the list of parameters to be added
        pass

    def do(self, x,y,curve=None):
        #This is the main engine, performing the calculation
        self.curve = curve
        return self.calculate(x,y)

    def calculate(self, x,y):
        pass

    def quickTest(self, c):
        #This function returns x/y arrays for showing the test/weight
        pass

    def disconnect(self):
        #disconnect the callback from the parameters
        for p in self._parameters.values():
            p.changed.disconnect()

    def connect(self, callback):
        #connect the callback to the parameters
        for p in self._parameters.values():
            p.changed.connect(callback)

    def getValue(self,name):
        return self._parameters[name].value

    def addParameter(self,name, widget):
        self._parameters[name] = widget

    def createUI(self, layout):
        while(layout.rowCount()>0):
            layout.removeRow(0)
        for widget in self._parameters.values():
            layout.addRow(str(widget.label), widget.native)

class fitPanel(boxPanel):
    def __init__(self):
        super().__init__()
        self.fitparameters = None

    def theory(self,x,*params):
        pass

    def getTheory(self,x,params,curve = None):
        self.curve = curve
        return self.theory(x,*params)

    def createUI(self,layout):
        mod = import_module(self.__class__.__module__)
        self.names=[]
        self.fitparameters = mod.PARAMETERS
        self.nparams = len(mod.PARAMETERS)
        for k in mod.PARAMETERS:
            self.names.append(k)
            self.addParameter(k, Label(name=k,label=mod.PARAMETERS[k]))
        super().createUI(layout)

    def setParameters(self,parameters):
        for i in range(len(parameters)):
            j = i-len(parameters)
            self._parameters[self.names[j]].value = str(parameters[i])
