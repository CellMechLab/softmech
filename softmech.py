import sys,os
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
import nano_view as view
import engine
import json
import protocols.filters,protocols.cpoint,protocols.fmodels,protocols.emodels


pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')


class NanoWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        self.ui = view.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ALLPLOTS = [self.ui.g_fz_all,self.ui.g_fz_single,self.ui.g_fizi_all,self.ui.g_fizi_single,self.ui.g_eze_all,self.ui.g_eze_single,self.ui.g_scatter1,self.ui.g_scatter2]
        self.workingpath = os.path.dirname(__file__)
        self.redraw = False

        self._filters_selected = []
        self._cpoint = None
        self._fmodel = None
        self._emodel = None

        self.loadPlugins()

        #main connections
        self.ui.b_load.clicked.connect(self.loadExperiment)
        self.ui.slid_cv.valueChanged.connect( self.selectedCurveChanged )
        self.ui.slid_alpha.valueChanged.connect( self.alphaChanged )
        self.ui.sel_filter.currentIndexChanged.connect(self.filterSelected)
        self.ui.tabfilters.tabCloseRequested.connect(self.removeFilter)
        self.ui.sel_cp.currentIndexChanged.connect(self.cpSelected)
        self.ui.sel_fmodel.currentIndexChanged.connect(self.fmodelSelect)
        self.ui.sel_emodel.currentIndexChanged.connect(self.emodelSelect)
        self.ui.setZeroForce.clicked.connect(self.calc1)
        self.ui.es_win.valueChanged.connect(self.calc1)
        self.ui.es_order.valueChanged.connect(self.calc1)
        self.ui.es_interpolate.clicked.connect(self.calc1)

        self.redraw = True
        QtCore.QMetaObject.connectSlotsByName(self)

    def reset(self):
        was = self.redraw
        self.redraw = False
        engine.dataset=[]
        for p in self.ALLPLOTS:
            p.clear()
            p.enableAutoRange( pg.ViewBox.XYAxes ,True)
        #set single curves 
        #FZ
        self._gc_fz_raw = pg.ScatterPlotItem(clickable=False)
        self._gc_fz_raw.setPen( pg.mkPen(0.7) )
        self._gc_fz_raw.setBrush(pg.mkBrush(0.5))
        self._gc_fz_raw.setSymbol('o')
        self.ui.g_fz_single.addItem(self._gc_fz_raw)
        self._gc_fz = pg.PlotCurveItem(clickable=False)
        self._gc_fz.setPen(pg.mkPen('k', width=1))
        self.ui.g_fz_single.addItem(self._gc_fz)
        #FiZi
        self._gc_fizi = pg.ScatterPlotItem(clickable=False)
        self._gc_fizi.setPen( pg.mkPen(0.7) )
        self._gc_fizi.setBrush(pg.mkBrush(0.5))
        self._gc_fizi.setSymbol('o')
        self.ui.g_fizi_single.addItem(self._gc_fizi)
        self._gc_fizi_fit = pg.PlotCurveItem(clickable=False)
        self._gc_fizi_fit.setPen(pg.mkPen('r', width=2, style=QtCore.Qt.DashLine))
        self.ui.g_fizi_single.addItem(self._gc_fizi_fit)
        #EZe
        self._gc_eze = pg.ScatterPlotItem(clickable=False)
        self._gc_eze.setPen( pg.mkPen(0.7) )
        self._gc_eze.setBrush(pg.mkBrush(0.5))
        self._gc_eze.setSymbol('o')
        self.ui.g_eze_single.addItem(self._gc_eze)
        self._gc_eze_fit = pg.PlotCurveItem(clickable=False)
        self._gc_eze_fit.setPen(pg.mkPen('r', width=2, style=QtCore.Qt.DashLine))
        self.ui.g_eze_single.addItem(self._gc_eze_fit)

        self.redraw = was

    def loadPlugins(self):
        data = protocols.filters.list()
        self._plugin_filters = list(data.keys())
        for l in data.values():
            self.ui.sel_filter.addItem(l)
        data = protocols.cpoint.list()
        self._plugin_cpoint = list(data.keys())
        for l in data.values():
            self.ui.sel_cp.addItem(l)
        data = protocols.fmodels.list()
        self._plugin_fmodels = list(data.keys())
        for l in data.values():
            self.ui.sel_fmodel.addItem(l)
        data = protocols.emodels.list()
        self._plugin_emodels = list(data.keys())
        for l in data.values():
            self.ui.sel_emodel.addItem(l)

    def getCol(self, col='k'):
        if col == 'k':
            col = [0,0,0]
        col.append( self.ui.slid_alpha.value() )
        return col

    def alphaChanged(self):
        for p in self.ui.g_fz_all.getPlotItem().listDataItems():
            p.setPen(pg.mkPen( self.getCol() ))
        for p in self.ui.g_fizi_all.getPlotItem().listDataItems():
            p.setPen(pg.mkPen( self.getCol() ))
        for p in self.ui.g_eze_all.getPlotItem().listDataItems():
            p.setPen(pg.mkPen( self.getCol() ))

    def loadExperiment(self):
        fOpener = QtWidgets.QFileDialog.getOpenFileName(self,"Open Experiment File",self.workingpath,"JSON curve files (*.json)")
        if fOpener[0]=='' or fOpener[0] is None:
            return
        self.redraw = False
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        filename = fOpener[0]
        self.workingpath = os.path.dirname(filename)
        self.reset()
        structure = json.load(open(filename))
        for cv in structure['curves']:
            engine.dataset.append(engine.curve(cv))
        i=0
        for cv in engine.dataset:
            #fz
            newcv = pg.PlotCurveItem(clickable=True)
            newcv.cvid = i
            newcv.sigClicked.connect(self.selectCurve)
            newcv.setPen( pg.mkPen( self.getCol() ) )
            self.ui.g_fz_all.addItem(newcv)
            #fizi
            newcv = pg.PlotCurveItem(clickable=True)
            newcv.cvid = i
            newcv.sigClicked.connect(self.selectCurve)
            newcv.setPen( pg.mkPen( self.getCol() ) )
            self.ui.g_fizi_all.addItem(newcv)
            #eze
            newcv = pg.PlotCurveItem(clickable=True)
            newcv.cvid = i
            newcv.sigClicked.connect(self.selectCurve)
            newcv.setPen( pg.mkPen( self.getCol() ) )
            self.ui.g_eze_all.addItem(newcv)
            i+=1
        self.ui.slid_cv.setMaximum(len(engine.dataset)-1)
        self.ui.slid_cv.setValue(0)
        self.redraw = True
        QtWidgets.QApplication.restoreOverrideCursor()
        self.calc0()   

    def selectCurve(self,cv):
        self.ui.slid_cv.setValue(cv.cvid)

    def selectedCurveChanged(self):
        if self.redraw is False:
            return
        if len(engine.dataset) == 0:
            return
        cC = engine.dataset[ int(self.ui.slid_cv.value()) ]
        #draw the selected fz curve
        self._gc_fz_raw.setData( cC.data['Z'],cC.data['F'] )
        #draw filtered
        self._gc_fz.setData(cC._Z,cC._F)        
        if cC._Zi is not None:
            #draw selected fizi
            self._gc_fizi.setData(cC._Zi,cC._Fi)
            #draw current fizi fit
            if cC._Fparams is not None:
                self._gc_fizi_fit.setData(cC._Zi,self._fmodel.theory(cC._Zi,*cC._Fparams,curve=cC))
        else:
            self._gc_fizi.setData([],[])
            self._gc_fizi_fit.setData([],[])
        if cC._Ze is not None:
                #draw selected eze
                self._gc_eze.setData(cC._Ze,cC._E)
                #draw current eze fit
                if cC._Eparams is not None:
                    self._gc_eze_fit.setData(cC._Ze,self._emodel.theory(cC._Ze,*cC._Eparams,curve=cC))
        else:
            self._gc_eze.setData([],[])
            self._gc_eze_fit.setData([],[])

    def calc_filters(self):
        for c in engine.dataset:
            c.reset()
            for fil in self._filters_selected:
                c.setZF(fil.calculate(c._Z,c._F,curve=c))

    def calc_cp(self):
        for c in engine.dataset:
            c.resetCP()
            cp = self._cpoint
            if cp is not None:
                ret = cp.calculate(c._Z,c._F,curve=c)
                if (ret is not None) and (ret is not False):
                    c._cp = ret    
                    c.calc_indentation(bool(self.ui.setZeroForce.isChecked()))
                    c.calc_elspectra(int(self.ui.es_win.value()),int(self.ui.es_order.value()),bool(self.ui.es_interpolate.isChecked()))                

    def calc_fmodels(self):
        for c in engine.dataset:
            c._Fparams = None
            model = self._fmodel
            if model is not None:
                ret = model.calculate(c._Zi,c._Fi,curve=c)
                if (ret is not None) and (ret is not False):
                    c._Fparams = ret 

    def calc_emodels(self):
        for c in engine.dataset:
            c._Eparams = None
            model = self._emodel
            if model is not None:
                ret = model.calculate(c._Ze,c._E,curve=c)
                if (ret is not None) and (ret is not False):
                    c._Eparams = ret

    def calc0(self):
        self.calculate()
        self.draw()
        self.selectedCurveChanged()

    def calc1(self):
        self.calculate(1)
        self.draw()
        self.selectedCurveChanged()

    def calculate(self,start=0):
        if self.redraw is False:
            return
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        if start == 0 or start == 'filters':
            self.calc_filters()
            self.calc_cp()
            self.calc_fmodels()
            self.calc_emodels()
        elif start == 1 or start == 'cp':
            self.calc_cp()
            self.calc_fmodels()
            self.calc_emodels()
        elif start == 2 or start == 'fmodel':
            self.calc_fmodels()
        elif start == 3 or start == 'emodel':
            self.calc_emodels()
        QtWidgets.QApplication.restoreOverrideCursor()

    def draw_fz(self):
        i=0
        for p in self.ui.g_fz_all.getPlotItem().listDataItems():
            c = engine.dataset[i]
            if c._cp is None:
                p.setData(c._Z,c._F)
            else:
                if self.ui.setZeroForce.isChecked() is True:
                    p.setData(c._Z-c._cp[0],c._F-c._cp[1])
                else:
                    p.setData(c._Z-c._cp[0],c._F)                
            i+=1

    def draw_fizi(self):
        i=0
        for p in self.ui.g_fizi_all.getPlotItem().listDataItems():
            c = engine.dataset[i]
            if c._Zi is None:
                p.setData([],[])
            else:
                p.setData(c._Zi,c._Fi)
            i+=1

    def draw_eze(self):
        i=0
        for p in self.ui.g_eze_all.getPlotItem().listDataItems():
            c = engine.dataset[i]
            if c._Ze is None:
                p.setData([],[])
            else:
                p.setData(c._Ze,c._E)
            i+=1

    def draw(self):
        if self.redraw is False:
            return
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        self.draw_fz()
        self.draw_fizi()
        self.draw_eze()       
        QtWidgets.QApplication.restoreOverrideCursor()  

    def data1(self):
        self.calculate(2)
        self.selectedCurveChanged()
        self.data()

    def data2(self):
        self.calculate(3)
        self.selectedCurveChanged()
        self.data()

    def data(self):
        pass

    def fmodelSelect(self,fid):
        if fid == 0:
            if self._fmodel is not None:                
                self._fmodel.disconnect()
                layout = self.ui.box_fmodel.layout()
                if layout is not None:
                    while(layout.rowCount()>0):
                        layout.removeRow(0)
                self._fmodel = None
        else:
            if self._fmodel is not None:                
                self._fmodel.disconnect()
            layout = self.ui.box_fmodel.layout()
            if layout is None:
                layout = QtWidgets.QFormLayout()
            self._fmodel = protocols.fmodels.get(self._plugin_fmodels[fid-1])
            self._fmodel.createUI(layout)
            self._fmodel.connect(self.data1)
            self.ui.box_fmodel.setLayout(layout)
        self.data1()

    def emodelSelect(self,fid):
        if fid == 0:
            if self._emodel is not None:                
                self._emodel.disconnect()
                layout = self.ui.box_emodel.layout()
                if layout is not None:
                    while(layout.rowCount()>0):
                        layout.removeRow(0)
                self._emodel = None
        else:
            if self._emodel is not None:                
                self._emodel.disconnect()
            layout = self.ui.box_emodel.layout()
            if layout is None:
                layout = QtWidgets.QFormLayout()
            self._emodel = protocols.emodels.get(self._plugin_emodels[fid-1])
            self._emodel.createUI(layout)
            self._emodel.connect(self.data2)
            self.ui.box_emodel.setLayout(layout)
        self.data2()

    def cpSelected(self,fid):
        if fid == 0:
            if self._cpoint is not None:                
                self._cpoint.disconnect()
                layout = self.ui.box_cp.layout()
                if layout is not None:
                    while(layout.rowCount()>0):
                        layout.removeRow(0)
                self._cpoint = None
        else:
            if self._cpoint is not None:                
                self._cpoint.disconnect()
            layout = self.ui.box_cp.layout()
            if layout is None:
                layout = QtWidgets.QFormLayout()
            self._cpoint = protocols.cpoint.get(self._plugin_cpoint[fid-1])
            self._cpoint.createUI(layout)
            self._cpoint.connect(self.calc1)
            self.ui.box_cp.setLayout(layout)
        self.calc1()

    def filterSelected(self,fid):
        if fid == 0:
            return
        name = self.ui.sel_filter.currentText()
        newfilter = protocols.filters.get(self._plugin_filters[fid-1])
        self._filters_selected.append( newfilter )
        newwidget = QtWidgets.QGroupBox()
        layout = QtWidgets.QFormLayout()
        layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self._filters_selected[-1].createUI(layout)
        newfilter.connect(self.calc0)
        newwidget.setLayout(layout)
        newtab = self.ui.tabfilters.addTab(newwidget,name)
        self.ui.tabfilters.setCurrentIndex(newtab)
        self.ui.sel_filter.setCurrentIndex(0)
        self.calc0()

    def removeFilter(self,fid):
        self.ui.tabfilters.removeTab(fid)
        self._filters_selected.pop(fid)
        self.calc0()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('SoftMech2021')
    app.setStyle('Fusion')
    chiaro = NanoWindow()
    chiaro.show()
    # QtCore.QObject.connect( app, QtCore.SIGNAL( 'lastWindowClosed()' ), app, QtCore.SLOT( 'quit()' ) )
    sys.exit(app.exec_())
