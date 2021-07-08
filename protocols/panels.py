from PyQt5 import QtGui, QtWidgets, QtCore
from importlib import import_module

class CPParameter:  # CP parameter class
    def __init__(self, label=None):
        self._label = label
        self._defaultValue = None
        self._validTypes = ['int', 'float', 'combo', 'label']
        self._type = 'int'
        self._values = []
        self._valueLabels = []
        self._widget = None
        self.triggered = None

    def getLabel(self):
        return self._label

    def getWidget(self):
        return self._widget

    def setType(self, t):
        if t in self._validTypes:
            self._type = t

    def setOptions(self, labels, values):
        self.setValueLabels(labels)
        self.setValues(values)

    def setValues(self, v):
        self._values = v

    def setValueLabels(self, v):
        self._valueLabels = v

    def getValue(self):
        pass

class CPPLabel(CPParameter):
    def __init__(self, label=None):
        super().__init__(label)
        self._defaultValue = ''
        self.setType('label')
        widget = QtWidgets.QLabel()
        widget.setTextFormat(QtCore.Qt.RichText)
        self._widget = widget
        self.setValue(self._defaultValue)
        self.triggered = None

    def setValue(self, text):
        self._widget.setText(str(text))

    def getValue(self):
        return self._widget.text()


class CPPInt(CPParameter):  # CPPInt inherits CPParameter class
    def __init__(self, label=None):
        super().__init__(label)
        self._defaultValue = 0
        self.setType('int')
        widget = QtWidgets.QLineEdit()
        valid = QtGui.QIntValidator()
        widget.setValidator(valid)
        self._widget = widget
        self.setValue(self._defaultValue)
        self.triggered = self._widget.editingFinished

    def setValue(self, num):
        self._widget.setText(str(int(num)))

    def getValue(self):
        return int(self._widget.text())


class CPPFloat(CPParameter):
    def __init__(self, label=None):
        super().__init__(label)
        self._defaultValue = 0.0
        self.setType('float')
        widget = QtWidgets.QLineEdit()
        valid = QtGui.QDoubleValidator()
        widget.setValidator(valid)
        self._widget = widget
        self.setValue(self._defaultValue)
        self.triggered = self._widget.editingFinished

    def setValue(self, num):
        self._widget.setText(str((num)))

    def getValue(self):
        return float(self._widget.text())


class CPPCombo(CPParameter):
    def __init__(self, label, dataset):
        super().__init__(label)
        self._defaultValue = 0
        self.setType('combo')


        self._values = list(dataset.keys())
        self._valueLabels = list(dataset.values())

        widget = QtWidgets.QComboBox()
        for v in dataset.values():
            widget.addItem(v)
        widget.setCurrentIndex(0)
        self._widget = widget
        self.triggered = self._widget.currentIndexChanged

    def getValue(self):
        who = int(self._widget.currentIndex())
        return float(self._values[who])

    def setValue(self, num):
        if num in self._values:
            for i in range(len(self._values)):
                if num == self._values[i]:
                    num = i
                    break
        self._widget.setCurrentIndex(num)

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
            if p.triggered is not None:
                p.triggered.disconnect()

    def connect(self, callback):
        #connect the callback to the parameters
        for p in self._parameters.values():
            if p.triggered is not None:
                p.triggered.connect(callback)

    def getValue(self,name):
        return self._parameters[name].getValue()

    def addParameter(self,name, ptype = 'Float', label='',value=0,dataset={}):
        #add a parameter to the form
        ptype = ptype.lower()
        if ptype == 'set':
            newpar = CPPCombo(label,dataset)
            newpar.setValue(value)
        elif ptype == 'int':
            newpar = CPPInt(label)
            newpar.setValue(value)
        elif ptype == 'float':
            newpar = CPPFloat(label)
            newpar.setValue(value)
        elif ptype == 'label':
            newpar = CPPLabel(label)
            newpar.setValue(value)
        self._parameters[name] = newpar

    def createUI(self, layout):
        while(layout.rowCount()>0):
            layout.removeRow(0)
        for widget in self._parameters.values():
            layout.addRow(widget.getLabel(), widget.getWidget())

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
            self.addParameter(k,'label',k,mod.PARAMETERS[k])
        super().createUI(layout)

    def setParameters(self,parameters):
        for i in range(len(parameters)):
            j = i-len(parameters)
            self._parameters[self.names[j]].setValue( str(parameters[i]) )
