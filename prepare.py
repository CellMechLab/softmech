import sys

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
import preparation.prepare_motor as motor
import mvexperiment.experiment as experiment
import preparation.prepare_view as view

import protocols.screening


pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

def emptyCurve():
    curve = {
        "filename": "noname",
        "date": "2021-12-02",
        "device_manufacturer": "Optics11",
        "tip":{
            "geometry": "sphere",
            "radius": 0.0
        },
        "spring_constant": 0.0, 
		"segment": "approach",
        "speed": 0.0,
        "data":{
            "F":[],
            "Z":[]
        }
    }
    return curve

def title_style(lab):
    return '<span style="font-family: Arial; font-weight:bold; font-size: 10pt;">{}</span>'.format(lab)

def lab_style(lab):
    return '<span style="">{}</span>'.format(lab)


class NanoWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        self.ui = view.Ui_radius()
        self.ui.setupUi(self)
        self.collection = None
        # set plots style
        self.curve_raw = pg.PlotCurveItem(clickable=False)
        self.curve_raw.setPen(
            pg.mkPen(pg.QtGui.QColor(0, 255, 0, 255), width=1))
        self.ui.g_single.plotItem.showGrid(True, True)
        self.ui.g_single.plotItem.addItem(self.curve_raw)
        self.curve_single = pg.PlotCurveItem(clickable=False)
        self.curve_single.setPen(
            pg.mkPen(pg.QtGui.QColor(0, 0, 0, 200), width=1))
        self.ui.g_single.plotItem.addItem(self.curve_single)
        self.curve_fit = pg.PlotCurveItem(clickable=False)
        self.curve_fit.setPen(pg.mkPen(pg.QtGui.QColor(
            0, 0, 255, 255), width=5, style=QtCore.Qt.DashLine))
        self.ui.g_single.plotItem.addItem(self.curve_fit)

        self.screening = None

        self.ui.g_fdistance.plotItem.setTitle(title_style('Raw curves'))
        self.ui.g_single.plotItem.setTitle(title_style('Current curve'))
        self.ui.g_fdistance.plotItem.setLabel('left', lab_style('Force [nN]'))
        self.ui.g_single.plotItem.setLabel('left', lab_style('Force [nN]'))
        self.ui.g_fdistance.plotItem.setLabel('bottom', lab_style('Displacement [nm]'))
        self.ui.g_single.plotItem.setLabel('bottom', lab_style('Displacement [nm]'))
        self.ui.save.clicked.connect(self.saveJSON)

        self.workingdir = './'
        self.collection = []
        self.experiment = None

        self._screening_selected = []
        data = protocols.screening.list()
        self._screening_methods = list(data.keys())
        for l in data.values():
            self.ui.cScreen.addItem(l)
        self.ui.cScreen.currentIndexChanged.connect(self.screenSelected)
        self.ui.tabScreen.tabCloseRequested.connect(self.removeScreen)

        # connect load and open, other connections after load/open
        self.ui.open_selectfolder.clicked.connect(self.open_folder)
        QtCore.QMetaObject.connectSlotsByName(self)

    def clear(self):
        self.collection = []
        self.experiment = None
        self.ui.mainlist.clear()
        self.ui.g_fdistance.plotItem.clear()
        self.curve_raw.setData(None)
        self.curve_single.setData(None)
        self.experiment = None
        self.collection = []

    def data_changed(self, item):
        included = item.checkState(0) == QtCore.Qt.Checked
        try:
            item.nano.included = included
        except AttributeError:
            pass

    # connecting all GUI events (signals) to respective slots (functions)
    def connect_all(self, connect=True):
        slots = []
        handlers = []

        slots.append(self.ui.curve_segment.valueChanged)
        handlers.append(self.refill)

        slots.append(self.ui.slid_alpha.valueChanged)
        handlers.append(self.set_alpha)

        slots.append(self.ui.mainlist.currentItemChanged)
        handlers.append(self.change_selected)

        slots.append(self.ui.mainlist.itemChanged)
        handlers.append(self.data_changed)

        cli = [self.ui.toggle_activated,
               self.ui.toggle_excluded, self.ui.toggle_activated]
        for click in cli:
            slots.append(click.clicked)
            handlers.append(self.toggle)

        slots.append(self.ui.crop.clicked)
        handlers.append(self.crop)

        for i in range(len(slots)):
            if connect is True:
                slots[i].connect(handlers[i])
            else:
                try:
                    slots[i].disconnect(handlers[i])
                except TypeError:
                    pass

    def disconnect_all(self):
        self.connect_all(False)

    def open_folder(self):
        fname = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Select the root dir', './')
        if fname == '' or fname is None or fname[0] == '':
            return

        QtWidgets.QApplication.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.WaitCursor))
        self.workingdir = fname

        exp = None
        quale = self.ui.c_open.currentText()
        if 'Optics11' in quale:
            if 'NEW' in quale:
                exp = experiment.Chiaro(fname)
            else:
                exp = experiment.ChiaroGenova(fname)
        elif 'Nanosurf' in quale:
            exp = experiment.NanoSurf(fname)
        elif 'TSV' in quale:
            exp = experiment.Easytsv(fname)
        # elif self.ui.jpk_open.isChecked() is True:
            #exp = experiment.Jpk(fname)

        exp.browse()
        if len(exp) == 0:
            QtWidgets.QApplication.restoreOverrideCursor()
            QtWidgets.QMessageBox.information(
                self, 'Empty folder', 'I did not find any valid file in the folder, please check file format and folder')
            return

        self.disconnect_all()
        self.clear()
        self.experiment = exp

        progress = QtWidgets.QProgressDialog(
            "Opening files...", "Cancel opening", 0, len(self.experiment.haystack))

        def attach(node, parent):
            myself = QtWidgets.QTreeWidgetItem(parent)
            node.myTree = myself
            myself.setText(0, node.basename)
            myself.curve = node
            myself.setFlags(
                myself.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
            myself.setCheckState(0, QtCore.Qt.Checked)
            for mychild in node:
                attach(mychild, myself)
        for node in self.experiment:
            attach(node, self.ui.mainlist)

        for c in self.experiment.haystack:
            c.open()
            node = motor.Nanoment(c)
            node.connect(self, c.myTree)
            c.myTree.nano = node
            self.collection.append(node)
            progress.setValue(progress.value() + 1)
            QtCore.QCoreApplication.processEvents()

        progress.setValue(len(self.experiment.haystack))
        QtWidgets.QApplication.restoreOverrideCursor()

        self.ui.springconstant.setValue(exp[0].cantilever_k)
        self.ui.tipradius.setValue(int(exp[0].tip_radius))
        if exp[0].tip_shape == 'sphere':
            self.ui.geometry.setCurrentIndex(1)
        elif exp.tip_shape == 'cylinder':
            self.ui.geometry.setCurrentIndex(2)
              # onest shapes are 'sphere' , 'cone' , 'flat'

        self.ui.curve_segment.setMaximum(len(self.experiment.haystack[0])-1)
        if len(self.experiment.haystack[0]) > 1:
            self.ui.curve_segment.setValue(1)
        self.connect_all()
        self.refill()

    def refresh(self):
        for c in self.collection:
            c.update_view()
        self.count()

    def toggle(self):
        current = 0
        for i in range(len(self.collection)):
            if self.collection[i].selected is True:
                current = i
                break
        if self.ui.toggle_activated.isChecked() is True:
            self.collection[current].active = True
        else:
            self.collection[current].active = False

    def crop(self):
        left = self.ui.crop_left.isChecked()
        right = self.ui.crop_right.isChecked()
        if left is True or right is True:
            # indicator = int(self.ui.curve_segment.value())
            for i in range(len(self.collection)):
                c = self.collection[i]
                try:
                    x = c._z_raw
                    y = c._f_raw
                    leftLim = np.min(c._z_raw) + 50
                    rightLim = np.max(c._z_raw) - 50
                    xnew = []
                    ynew = []
                    for k in range(len(x)):
                        this = True
                        if left is True:
                            if x[k] < leftLim:
                                this = False
                        if right is True:
                            if x[k] > rightLim:
                                this = False
                        if this is True:
                            xnew.append(x[k])
                            ynew.append(y[k])
                    self.collection[i].set_XY(xnew, ynew)
                except IndexError:
                    QtWidgets.QMessageBox.information(
                        self, 'Empty curve', 'Problem detected with curve {}, not populated'.format(c.basename))
        else:
            return

    def refill(self):
        indicator = int(self.ui.curve_segment.value())
        for i in range(len(self.collection)):
            c = self.experiment.haystack[i]
            try:
                self.collection[i].set_XY(c[indicator].z, c[indicator].f)
            except IndexError:
                QtWidgets.QMessageBox.information(
                    self, 'Empty curve', 'Problem detected with curve {}, not populated'.format(c.basename))

    def curve_clicked(self, curve):
        for c in self.collection:
            c.selected = False
        curve.nano.selected = True

    def change_selected(self, item):
        for c in self.collection:
            c.selected = False
        try:
            item.nano.selected = True
        except AttributeError:
            pass

    def set_alpha(self, num):
        num = int(num)
        for c in self.collection:
            c.alpha = num

    def screenSelected(self,fid):
        if fid == 0:
            return
        name = self.ui.cScreen.currentText()
        newfilter = protocols.screening.get(self._screening_methods[fid-1])
        self._screening_selected.append( newfilter )
        newwidget = QtWidgets.QGroupBox()
        layout = QtWidgets.QFormLayout()
        layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self._screening_selected[-1].createUI(layout)
        newfilter.connect(self.doScreen)
        newwidget.setLayout(layout)
        newtab = self.ui.tabScreen.addTab(newwidget,name)
        self.ui.tabScreen.setCurrentIndex(newtab)
        self.ui.cScreen.setCurrentIndex(0)
        self.doScreen()

    def removeScreen(self,fid):
        self.ui.tabScreen.removeTab(fid)
        self._screening_selected.pop(fid)
        self.doScreen()

    def doScreen(self):
        for c in self.collection:
            c.active = True
        for method in self._screening_selected:
            for c in self.collection:
                if c.active is True:
                    c.active = method.calculate(c._z*1e-9,c._f*1e-9)

    def saveJSON(self):

        #fname = QtWidgets.QFileDialog.getSaveFileName(self, 'Save the experiment to a JSON structure', './')
        fname = QtWidgets.QFileDialog.getSaveFileName(self, 'Save the experiment to a JSON structure', self.workingdir, "JSON Files (*.json)")
        if fname == '' or fname is None or fname[0] == '':
            return

        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        
        import json
        curves = []

        geometry = str(self.ui.geometry.currentText()).lower()
        radius = radius = float(self.ui.tipradius.value())
        spring = float(self.ui.springconstant.value())

        for c in self.collection:
            if c.active is True:    
                cv = emptyCurve()
                cv['filename']=c.basename                
                cv['tip']['radius']=radius*1e-9
                cv['tip']['geometry']=geometry
                cv['spring_constant']=spring
                cv['data']['Z']=list(c._z*1e-9)
                cv['data']['F']=list(c._f*1e-9)
                curves.append(cv)
        exp = {'Description':'Optics11 data'}
        pro = {}
        json.dump({'experiment':exp,'protocol':pro,'curves':curves},open(fname[0],'w'))
        QtWidgets.QApplication.restoreOverrideCursor()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('Nano2021')
    app.setStyle('Fusion')
    chiaro = NanoWindow()
    chiaro.show()
    # QtCore.QObject.connect( app, QtCore.SIGNAL( 'lastWindowClosed()' ), app, QtCore.SLOT( 'quit()' ) )
    sys.exit(app.exec_())
