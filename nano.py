import sys,os
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
useQtmodern = False
try:
    import qtmodern.styles
    import qtmodern.windows
    useQtmodern = True
except ModuleNotFoundError:
    print('Module qtmodern not found. Please evaluate installing it for a nicer UI')

import nanoindentation.nano_view as view
import nanoindentation.engine as engine
import json
import protocols.filters,protocols.cpoint,protocols.fmodels,protocols.emodels

useGevent = False
try:
    from gevent import monkey; monkey.patch_all()   # noqa
    import gevent
    from pyqtconsole.console import PythonConsole
    useGevent = True
except ModuleNotFoundError:
    print('Module gevent and/or pyqtconsole not found. Please evaluate installing it if you want to have access to the integrated shell')

try:
    from magicgui.widgets import Spinbox   # noqa
except ModuleNotFoundError:
    print('Module magicgui is not installed. You need it to load the plugins from the corresponding folders!!!')



pg.setConfigOption('background', (53,53,53))
pg.setConfigOption('foreground', 'w')

#circles
COL_CIR_OUTER=[42, 130, 218]
COL_CIR_INNER=[42, 130, 218, 100]
#lines
COL_LIN = [250, 94, 82]
COL_LIN_FIT = [255, 255, 0]

def roundCol(i):    
    col = []
    #to test and change
    col.append([42, 130, 218])
    col.append([250, 94, 82])
    col.append([255, 255, 0])
    col.append([255,255,255])
    return col[i%len(col)]

class GEventProcessing:

    """Interoperability class between Qt/gevent that allows processing gevent
    tasks during Qt idle periods."""

    def __init__(self, idle_period=0.010):
        # Limit the IDLE handler's frequency while still allow for gevent
        # to trigger a microthread anytime
        self._idle_period = idle_period
        # IDLE timer: on_idle is called whenever no Qt events left for
        # processing
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.process_events)
        self._timer.start(0)

    def __enter__(self):
        pass

    def __exit__(self, *exc_info):
        self._timer.stop()

    def process_events(self):
        # Cooperative yield, allow gevent to monitor file handles via libevent
        gevent.sleep(self._idle_period)

class NanoWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.app = app
        self.ui = view.Ui_MainWindow()
        self.ui.setupUi(self)
        #self.setStyleSheet("background-color: grey") 
        self.ALLPLOTS = [self.ui.g_fz_all,self.ui.g_fz_single,self.ui.g_fizi_all,self.ui.g_fizi_single,self.ui.g_eze_all,self.ui.g_eze_single,self.ui.g_scatter1,self.ui.g_scatter2]
        self.workingpath = os.path.dirname(__file__)
        self.redraw = False

        self._filters_selected = []
        self._cpoint = None
        self._fmodel = None
        self._emodel = None
        self._fdata = None
        self._edata = None

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
        self.ui.zi_min.valueChanged.connect(self.data1)
        self.ui.zi_max.valueChanged.connect(self.data1)
        self.ui.ze_min.valueChanged.connect(self.data2)
        self.ui.ze_max.valueChanged.connect(self.data2)
        self.ui.b_saveFdata.clicked.connect(lambda: self.save_params(True))
        self.ui.b_saveEdata.clicked.connect(lambda: self.save_params(False))
        self.redraw = True        
        QtCore.QMetaObject.connectSlotsByName(self)

        if useGevent is True:
            self.ui.consolle.clicked.connect(self.new_consolle)

    def getData(self):
        return engine.dataset

    def getCurrent(self):
        cC = engine.dataset[ int(self.ui.slid_cv.value()) ]
        dummy = {'indentation':None,'ind_fit':None,'elastography':None,'el_fit':None}
        dummy['src']=cC
        dummy['curve']=(cC._Z,cC._F)
        if cC._Zi is not None:
            dummy['indentation']=(cC._Zi,cC._Fi)
            if cC._Fparams is not None:                
                x,y = cC.getFizi(self.ui.zi_min.value()*1e-9,self.ui.zi_max.value()*1e-9)
                dummy['ind_fit']=(x,self._fmodel.getTheory(x,cC._Fparams,curve=cC))
        if cC._Ze is not None:
                dummy['elastography']=(cC._Ze,cC._E)
                if cC._Eparams is not None:
                    x,y = cC.getEze(self.ui.ze_min.value()*1e-9,self.ui.ze_max.value()*1e-9)
                    dummy['el_fit']=(x,self._emodel.getTheory(x,cC._Eparams,curve=cC))
        return dummy 
        
    def new_consolle(self):
        self.a=[]
        console = PythonConsole()
        console.push_local_ns('getData', self.getData)
        console.push_local_ns('getCurrent', self.getCurrent)
        console.show()
        console.eval_executor(gevent.spawn)

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
        self._gc_fz_raw.setPen( pg.mkPen(COL_CIR_OUTER) )
        self._gc_fz_raw.setBrush(pg.mkBrush(COL_CIR_INNER))
        self._gc_fz_raw.setSymbol('o')
        self.ui.g_fz_single.addItem(self._gc_fz_raw)
        self._gc_fz = pg.PlotCurveItem(clickable=False)
        self._gc_fz.setPen(pg.mkPen(COL_LIN, width=4))
        self.ui.g_fz_single.addItem(self._gc_fz)
        #FiZi
        self._gc_fizi = pg.ScatterPlotItem(clickable=False)
        self._gc_fizi.setPen( pg.mkPen(COL_CIR_OUTER) )
        self._gc_fizi.setBrush(pg.mkBrush(COL_CIR_INNER))
        self._gc_fizi.setSymbol('o')
        self.ui.g_fizi_single.addItem(self._gc_fizi)
        self._gc_fizi_fit = pg.PlotCurveItem(clickable=False)
        self._gc_fizi_fit.setPen(pg.mkPen(COL_LIN_FIT, width=6)) #style=QtCore.Qt.DashLine
        self.ui.g_fizi_single.addItem(self._gc_fizi_fit)
        #EZe
        self._gc_eze = pg.ScatterPlotItem(clickable=False)
        self._gc_eze.setPen( pg.mkPen(COL_CIR_OUTER) )
        self._gc_eze.setBrush(pg.mkBrush(COL_CIR_INNER))
        self._gc_eze.setSymbol('o')
        self.ui.g_eze_single.addItem(self._gc_eze)
        self._gc_eze_fit = pg.PlotCurveItem(clickable=False)
        self._gc_eze_fit.setPen(pg.mkPen(COL_LIN_FIT, width=6)) #style=QtCore.Qt.DashLine
        self.ui.g_eze_single.addItem(self._gc_eze_fit)
        
        self.redraw = was

        #Titles and labels (single and all)
        def title_style(lab):
            return '<span style="font-family: Arial; font-weight:bold; font-size: 10pt;">{}</span>'.format(lab)

        def lab_style(lab):
            return '<span style="">{}</span>'.format(lab)
        #FZ single
        self.ui.g_fz_single.setTitle(title_style('Force-displacement (single)'))
        self.ui.g_fz_single.setLabel('left', lab_style('F [N]'))
        self.ui.g_fz_single.setLabel('bottom', lab_style('z [m]'))
        #FiZi single
        self.ui.g_fizi_single.setTitle(title_style('Force-indentation (single)'))
        self.ui.g_fizi_single.setLabel('left', lab_style('F [N]'))
        self.ui.g_fizi_single.setLabel('bottom', lab_style('<font>&delta;</font> [m]'))
        #EZe single
        self.ui.g_eze_single.setTitle(title_style('Elasticity Spectra (single)'))
        self.ui.g_eze_single.setLabel('left', lab_style('E [Pa]'))
        self.ui.g_eze_single.setLabel('bottom', lab_style('<font>&delta;</font> [m]'))
        
        #FZ all
        self.ui.g_fz_all.setTitle(title_style('Force-displacement (data set)'))
        self.ui.g_fz_all.setLabel('left', lab_style('F [N]'))
        self.ui.g_fz_all.setLabel('bottom', lab_style('z [m]'))
        #FiZi all
        self.ui.g_fizi_all.setTitle(title_style('Force-indentation (data set)'))
        self.ui.g_fizi_all.setLabel('left', lab_style('F [N]'))
        self.ui.g_fizi_all.setLabel('bottom', lab_style('<font>&delta;</font> [m]'))
        #EZe
        self.ui.g_eze_all.setTitle(title_style('Elasticity Spectra (data set)'))
        self.ui.g_eze_all.setLabel('left', lab_style('E [Pa]'))
        self.ui.g_eze_all.setLabel('bottom', lab_style('<font>&delta;</font> [m]'))

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

    def getCol(self, col=COL_LIN):
        colalpha = [0,0,0,self.ui.slid_alpha.value()]
        colalpha[0:3]=col
        return colalpha

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
                x,y = cC.getFizi(self.ui.zi_min.value()*1e-9,self.ui.zi_max.value()*1e-9)
                self._gc_fizi_fit.setData(x,self._fmodel.getTheory(x,cC._Fparams,curve=cC))                
        else:
            self._gc_fizi.setData([],[])
            self._gc_fizi_fit.setData([],[])
        if cC._Ze is not None:
                #draw selected eze
                self._gc_eze.setData(cC._Ze,cC._E)
                #draw current eze fit
                if cC._Eparams is not None:
                    x,y = cC.getEze(self.ui.ze_min.value()*1e-9,self.ui.ze_max.value()*1e-9)
                    self._gc_eze_fit.setData(x,self._emodel.getTheory(x,cC._Eparams,curve=cC))
        else:
            self._gc_eze.setData([],[])
            self._gc_eze_fit.setData([],[])

    def calc_filters(self):
        for c in engine.dataset:
            c.reset()            
            for fil in self._filters_selected:
                try:
                    c.setZF(fil.do(c._Z,c._F,curve=c))
                except  Exception as e:
                    print('Error filtering the curve: ',e)

    def calc_cp(self):
        for c in engine.dataset:
            c.resetCP()
            cp = self._cpoint
            if cp is not None:
                try:
                    ret = cp.do(c._Z,c._F,curve=c)
                    if (ret is not None) and (ret is not False):
                        c._cp = ret    
                        c.calc_indentation(bool(self.ui.setZeroForce.isChecked()))
                        c.calc_elspectra(int(self.ui.es_win.value()),int(self.ui.es_order.value()),bool(self.ui.es_interpolate.isChecked()))                
                except Exception as e:
                    print('ERROR calculating the contact point: ',e)

    def calc_fmodels(self):
        for c in engine.dataset:
            c._Fparams = None
            model = self._fmodel
            if model is not None:
                try:
                    x,y = c.getFizi(self.ui.zi_min.value()*1e-9,self.ui.zi_max.value()*1e-9)            
                    ret = model.do(x,y,curve=c)
                    if (ret is not None) and (ret is not False):
                        c._Fparams = ret 
                except Exception as e:
                    print('Error in the force model: ',e)

    def calc_emodels(self):
        for c in engine.dataset:
            c._Eparams = None
            model = self._emodel
            if model is not None:                
                try:
                    x,y = c.getEze(self.ui.ze_min.value()*1e-9,self.ui.ze_max.value()*1e-9)
                    ret = model.do(x,y,curve=c)
                    if (ret is not None) and (ret is not False):
                        c._Eparams = ret
                except Exception as e:
                    print('Error in the E model: ',e)

    def calc0(self):
        self.calculate()
        self.draw()
        self.selectedCurveChanged()
        self.data()

    def calc1(self):
        self.calculate(1)
        self.draw()
        self.selectedCurveChanged()
        self.data()

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
        self.fdata = None
        self.edata = None
        fmod = []
        nfmod = 0
        for cC in engine.dataset:
            if cC._Fparams is not None:
                fmod.append(cC._Fparams)
                if nfmod == 0:
                    nfmod = len(cC._Fparams)
        if nfmod>0:
            self.fdata = engine.reorganise(fmod,nfmod)
            self._fmodel.setParameters(engine.dataformat(self.fdata,nfmod))            
        emod = []
        nemod = 0
        for cC in engine.dataset:
            if cC._Eparams is not None:
                emod.append(cC._Eparams)
                if nemod == 0:
                    nemod = len(cC._Eparams)
        if nemod>0:
            self.edata = engine.reorganise(emod,nemod)
            self._emodel.setParameters(engine.dataformat(self.edata,nemod))
        self.scatter()

    def save_params(self,force = True):
        if force is True:
            if self.fdata is None or self.fdata is False or len(self.fdata) == 0:
                return
        else:
            if self.edata is None or self.edata is False or len(self.edata) == 0:
                return

        fname = QtWidgets.QFileDialog.getSaveFileName(self, 'Save the data to a CSV datafile', self.workingpath, "CSV Files (*.csv)")
        if fname == '' or fname is None or fname[0] == '':
            return        

        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        if force is True:
            header = '#SoftMech export data\n#Indentation analysis\n#\n#FModel parameters\n'
            model = self._fmodel
            data = self.fdata
        else:
            header = '#SoftMech export data\n#Elastography analysis\n#\n#EModel parameters\n'
            model = self._emodel
            data = self.edata
        
        f = open(fname[0],'w')

        for key in model.fitparameters:
            header += '#{}:{}\n'.format(key,model.fitparameters[key])
        header+='#\n#'
        pre = ''
        for key in model.fitparameters:
            header = header + pre + key
            pre = ','
        header+='\n#\n#DATA\n'
        f.write(header)
        for line in range(len(data[0])):
            pre = ''
            for column in range(len(data)):
                f.write(pre + str(data[column][line]))
                pre=','
            f.write('\n')
        f.close()
        QtWidgets.QApplication.restoreOverrideCursor()

    def scatter(self):
        self.ui.g_scatter1.plotItem.clear()
        self.ui.g_scatter2.plotItem.clear()
        if self._fmodel is not None:
            for i in range(self._fmodel.nparams):
                w = self.ui.f_params.layout().itemAt(i)
                if w is not None:
                    if w.widget().isChecked() is True:
                        sc = pg.ScatterPlotItem(clickable = False)
                        col = roundCol(i)
                        sc.setPen(pg.mkPen(col))
                        col.append(100)
                        sc.setBrush(pg.mkBrush(col))
                        sc.setData(engine.np.linspace(0,len(self.fdata[i]),len(self.fdata[i])),self.fdata[i] )
                        self.ui.g_scatter1.addItem(sc) 
                        self.ui.g_scatter1.plotItem.setLabel('bottom', 'Curve [#]')
        if self._emodel is not None:
            for i in range(self._emodel.nparams):
                w = self.ui.e_params.layout().itemAt(i)
                if w is not None:
                    if w.widget().isChecked() is True:
                        sc = pg.ScatterPlotItem(clickable = False)
                        col = roundCol(i)
                        sc.setPen( pg.mkPen(col) )
                        col.append(100)
                        sc.setBrush(pg.mkBrush(col))
                        sc.setData( engine.np.linspace(0,len(self.edata[i]),len(self.edata[i])),self.edata[i] )
                        self.ui.g_scatter2.addItem(sc) 
                        self.ui.g_scatter2.plotItem.setLabel('bottom', 'Curve [#]')

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
        self.clearData(1)
        self.createData(1)
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
        self.clearData(2)
        self.createData(2)
        self.data2()

    def clearData(self,where):
        if where ==1:            
            layout = self.ui.f_params.layout()
        else:
            layout = self.ui.e_params.layout()
        if layout is not None:
            while layout.count() > 0:
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    def createData(self,where):
        if where ==1:
            layout = self.ui.f_params.layout()
        else:
            layout = self.ui.e_params.layout()
        if layout is None:
            layout = QtWidgets.QVBoxLayout()
        if where ==1:
            if self._fmodel is not None:
                for k,v in self._fmodel.fitparameters.items():
                    chk = QtWidgets.QCheckBox(k)
                    chk.clicked.connect(self.scatter)
                    layout.addWidget(chk)
        else:
            if self._emodel is not None:
                for k,v in self._emodel.fitparameters.items():
                    chk = QtWidgets.QCheckBox(k)
                    chk.clicked.connect(self.scatter)
                    layout.addWidget(chk)
        if where ==1:
            if self.ui.f_params.layout() is None:
                self.ui.f_params.setLayout(layout)
        else:
            if self.ui.e_params.layout() is None:
                self.ui.e_params.setLayout(layout)

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
    if useQtmodern is True:
        qtmodern.styles.dark(app)
        chiaro = NanoWindow()
        mw = qtmodern.windows.ModernWindow(chiaro)
    else:
        mw = NanoWindow()
    mw.show()

    #app.setQuitOnLastWindowClosed(True)
    #app.aboutToQuit.connect(chiaro.cleanup_consoles)

    #chiaro.ipkernel.start()
    #sys.exit(app.exec_())
    if useGevent is True:
        with GEventProcessing():
            sys.exit(app.exec_())
    else:
        sys.exit(app.exec_())
