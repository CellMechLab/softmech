# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'nano_new.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QSizePolicy, QSlider,
    QSpacerItem, QSpinBox, QSplitter, QStatusBar,
    QTabWidget, QToolBox, QVBoxLayout, QWidget)

from pyqtgraph import PlotWidget

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1680, 917)
        icon = QIcon()
        icon.addFile(u"ico.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_10 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        self.splitter.setSizePolicy(sizePolicy)
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setHandleWidth(7)
        self.toolBox = QToolBox(self.splitter)
        self.toolBox.setObjectName(u"toolBox")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.toolBox.sizePolicy().hasHeightForWidth())
        self.toolBox.setSizePolicy(sizePolicy1)
        self.toolBoxPage1 = QWidget()
        self.toolBoxPage1.setObjectName(u"toolBoxPage1")
        self.toolBoxPage1.setGeometry(QRect(0, 0, 155, 641))
        self.verticalLayout = QVBoxLayout(self.toolBoxPage1)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.b_load = QPushButton(self.toolBoxPage1)
        self.b_load.setObjectName(u"b_load")

        self.verticalLayout.addWidget(self.b_load)

        self.updateexperiment = QPushButton(self.toolBoxPage1)
        self.updateexperiment.setObjectName(u"updateexperiment")
        self.updateexperiment.setEnabled(False)

        self.verticalLayout.addWidget(self.updateexperiment)

        self.consolle = QPushButton(self.toolBoxPage1)
        self.consolle.setObjectName(u"consolle")

        self.verticalLayout.addWidget(self.consolle)

        self.b_protocol = QPushButton(self.toolBoxPage1)
        self.b_protocol.setObjectName(u"b_protocol")
        self.b_protocol.setEnabled(False)

        self.verticalLayout.addWidget(self.b_protocol)

        self.verticalSpacer_2 = QSpacerItem(20, 723, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.toolBox.addItem(self.toolBoxPage1, u"Load")
        self.toolBoxPage2 = QWidget()
        self.toolBoxPage2.setObjectName(u"toolBoxPage2")
        self.toolBoxPage2.setGeometry(QRect(0, 0, 145, 49))
        self.verticalLayout_2 = QVBoxLayout(self.toolBoxPage2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.sel_filter = QComboBox(self.toolBoxPage2)
        self.sel_filter.addItem("")
        self.sel_filter.setObjectName(u"sel_filter")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.sel_filter.sizePolicy().hasHeightForWidth())
        self.sel_filter.setSizePolicy(sizePolicy2)
        self.sel_filter.setLayoutDirection(Qt.LeftToRight)
        self.sel_filter.setAutoFillBackground(False)
        self.sel_filter.setFrame(True)

        self.verticalLayout_2.addWidget(self.sel_filter)

        self.tabfilters = QTabWidget(self.toolBoxPage2)
        self.tabfilters.setObjectName(u"tabfilters")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.tabfilters.sizePolicy().hasHeightForWidth())
        self.tabfilters.setSizePolicy(sizePolicy3)
        self.tabfilters.setTabPosition(QTabWidget.North)
        self.tabfilters.setUsesScrollButtons(True)
        self.tabfilters.setDocumentMode(False)
        self.tabfilters.setTabsClosable(True)
        self.tabfilters.setMovable(True)
        self.tabfilters.setTabBarAutoHide(False)

        self.verticalLayout_2.addWidget(self.tabfilters)

        self.toolBox.addItem(self.toolBoxPage2, u"Filters")
        self.toolBoxPage3 = QWidget()
        self.toolBoxPage3.setObjectName(u"toolBoxPage3")
        self.toolBoxPage3.setGeometry(QRect(0, 0, 117, 86))
        self.verticalLayout_3 = QVBoxLayout(self.toolBoxPage3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.sel_cp = QComboBox(self.toolBoxPage3)
        self.sel_cp.addItem("")
        self.sel_cp.setObjectName(u"sel_cp")
        sizePolicy2.setHeightForWidth(self.sel_cp.sizePolicy().hasHeightForWidth())
        self.sel_cp.setSizePolicy(sizePolicy2)

        self.verticalLayout_3.addWidget(self.sel_cp)

        self.box_cp = QGroupBox(self.toolBoxPage3)
        self.box_cp.setObjectName(u"box_cp")
        sizePolicy2.setHeightForWidth(self.box_cp.sizePolicy().hasHeightForWidth())
        self.box_cp.setSizePolicy(sizePolicy2)

        self.verticalLayout_3.addWidget(self.box_cp)

        self.setZeroForce = QCheckBox(self.toolBoxPage3)
        self.setZeroForce.setObjectName(u"setZeroForce")
        self.setZeroForce.setChecked(True)

        self.verticalLayout_3.addWidget(self.setZeroForce)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.toolBox.addItem(self.toolBoxPage3, u"Contact point")
        self.toolBoxPage4 = QWidget()
        self.toolBoxPage4.setObjectName(u"toolBoxPage4")
        self.toolBoxPage4.setGeometry(QRect(0, 0, 143, 133))
        self.verticalLayout_6 = QVBoxLayout(self.toolBoxPage4)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.sel_fmodel = QComboBox(self.toolBoxPage4)
        self.sel_fmodel.addItem("")
        self.sel_fmodel.setObjectName(u"sel_fmodel")
        sizePolicy2.setHeightForWidth(self.sel_fmodel.sizePolicy().hasHeightForWidth())
        self.sel_fmodel.setSizePolicy(sizePolicy2)

        self.verticalLayout_6.addWidget(self.sel_fmodel)

        self.box_fmodel = QGroupBox(self.toolBoxPage4)
        self.box_fmodel.setObjectName(u"box_fmodel")
        sizePolicy2.setHeightForWidth(self.box_fmodel.sizePolicy().hasHeightForWidth())
        self.box_fmodel.setSizePolicy(sizePolicy2)

        self.verticalLayout_6.addWidget(self.box_fmodel)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label_9 = QLabel(self.toolBoxPage4)
        self.label_9.setObjectName(u"label_9")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_9)

        self.zi_min = QSpinBox(self.toolBoxPage4)
        self.zi_min.setObjectName(u"zi_min")
        self.zi_min.setMinimum(0)
        self.zi_min.setMaximum(9999)
        self.zi_min.setValue(0)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.zi_min)

        self.label_11 = QLabel(self.toolBoxPage4)
        self.label_11.setObjectName(u"label_11")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_11)

        self.zi_max = QSpinBox(self.toolBoxPage4)
        self.zi_max.setObjectName(u"zi_max")
        self.zi_max.setMinimum(0)
        self.zi_max.setMaximum(9999)
        self.zi_max.setValue(800)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.zi_max)


        self.verticalLayout_6.addLayout(self.formLayout)

        self.f_params = QGroupBox(self.toolBoxPage4)
        self.f_params.setObjectName(u"f_params")
        sizePolicy3.setHeightForWidth(self.f_params.sizePolicy().hasHeightForWidth())
        self.f_params.setSizePolicy(sizePolicy3)

        self.verticalLayout_6.addWidget(self.f_params)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer_3)

        self.toolBox.addItem(self.toolBoxPage4, u"Force model")
        self.toolBoxPage5 = QWidget()
        self.toolBoxPage5.setObjectName(u"toolBoxPage5")
        self.toolBoxPage5.setGeometry(QRect(0, 0, 116, 94))
        self.verticalLayout_7 = QVBoxLayout(self.toolBoxPage5)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_13 = QLabel(self.toolBoxPage5)
        self.label_13.setObjectName(u"label_13")
        sizePolicy3.setHeightForWidth(self.label_13.sizePolicy().hasHeightForWidth())
        self.label_13.setSizePolicy(sizePolicy3)

        self.horizontalLayout_3.addWidget(self.label_13)

        self.es_interpolate = QCheckBox(self.toolBoxPage5)
        self.es_interpolate.setObjectName(u"es_interpolate")
        self.es_interpolate.setChecked(True)

        self.horizontalLayout_3.addWidget(self.es_interpolate)


        self.verticalLayout_7.addLayout(self.horizontalLayout_3)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_21 = QLabel(self.toolBoxPage5)
        self.label_21.setObjectName(u"label_21")
        sizePolicy3.setHeightForWidth(self.label_21.sizePolicy().hasHeightForWidth())
        self.label_21.setSizePolicy(sizePolicy3)

        self.horizontalLayout.addWidget(self.label_21)

        self.es_order = QSpinBox(self.toolBoxPage5)
        self.es_order.setObjectName(u"es_order")
        self.es_order.setMinimum(1)
        self.es_order.setMaximum(9)
        self.es_order.setValue(2)

        self.horizontalLayout.addWidget(self.es_order)


        self.verticalLayout_7.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_8 = QLabel(self.toolBoxPage5)
        self.label_8.setObjectName(u"label_8")
        sizePolicy3.setHeightForWidth(self.label_8.sizePolicy().hasHeightForWidth())
        self.label_8.setSizePolicy(sizePolicy3)

        self.horizontalLayout_2.addWidget(self.label_8)

        self.es_win = QSpinBox(self.toolBoxPage5)
        self.es_win.setObjectName(u"es_win")
        self.es_win.setMinimum(3)
        self.es_win.setMaximum(9999)
        self.es_win.setValue(61)

        self.horizontalLayout_2.addWidget(self.es_win)


        self.verticalLayout_7.addLayout(self.horizontalLayout_2)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_7.addItem(self.verticalSpacer_4)

        self.toolBox.addItem(self.toolBoxPage5, u"Elasticity spectra")
        self.toolBoxPage6 = QWidget()
        self.toolBoxPage6.setObjectName(u"toolBoxPage6")
        self.toolBoxPage6.setGeometry(QRect(0, 0, 143, 133))
        self.verticalLayout_8 = QVBoxLayout(self.toolBoxPage6)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.sel_emodel = QComboBox(self.toolBoxPage6)
        self.sel_emodel.addItem("")
        self.sel_emodel.setObjectName(u"sel_emodel")
        sizePolicy2.setHeightForWidth(self.sel_emodel.sizePolicy().hasHeightForWidth())
        self.sel_emodel.setSizePolicy(sizePolicy2)

        self.verticalLayout_8.addWidget(self.sel_emodel)

        self.box_emodel = QGroupBox(self.toolBoxPage6)
        self.box_emodel.setObjectName(u"box_emodel")
        sizePolicy2.setHeightForWidth(self.box_emodel.sizePolicy().hasHeightForWidth())
        self.box_emodel.setSizePolicy(sizePolicy2)

        self.verticalLayout_8.addWidget(self.box_emodel)

        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label_12 = QLabel(self.toolBoxPage6)
        self.label_12.setObjectName(u"label_12")
        sizePolicy3.setHeightForWidth(self.label_12.sizePolicy().hasHeightForWidth())
        self.label_12.setSizePolicy(sizePolicy3)

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_12)

        self.ze_min = QSpinBox(self.toolBoxPage6)
        self.ze_min.setObjectName(u"ze_min")
        self.ze_min.setMinimum(0)
        self.ze_min.setMaximum(9999)
        self.ze_min.setValue(0)

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.ze_min)

        self.label_14 = QLabel(self.toolBoxPage6)
        self.label_14.setObjectName(u"label_14")
        sizePolicy3.setHeightForWidth(self.label_14.sizePolicy().hasHeightForWidth())
        self.label_14.setSizePolicy(sizePolicy3)

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.label_14)

        self.ze_max = QSpinBox(self.toolBoxPage6)
        self.ze_max.setObjectName(u"ze_max")
        self.ze_max.setMinimum(0)
        self.ze_max.setMaximum(9999)
        self.ze_max.setValue(800)

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.ze_max)


        self.verticalLayout_8.addLayout(self.formLayout_3)

        self.e_params = QGroupBox(self.toolBoxPage6)
        self.e_params.setObjectName(u"e_params")
        sizePolicy3.setHeightForWidth(self.e_params.sizePolicy().hasHeightForWidth())
        self.e_params.setSizePolicy(sizePolicy3)

        self.verticalLayout_8.addWidget(self.e_params)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer_5)

        self.toolBox.addItem(self.toolBoxPage6, u"Elasticity Model")
        self.toolBoxPage7 = QWidget()
        self.toolBoxPage7.setObjectName(u"toolBoxPage7")
        self.toolBoxPage7.setGeometry(QRect(0, 0, 176, 93))
        self.verticalLayout_9 = QVBoxLayout(self.toolBoxPage7)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.sel_exp = QComboBox(self.toolBoxPage7)
        self.sel_exp.addItem("")
        self.sel_exp.setObjectName(u"sel_exp")
        sizePolicy2.setHeightForWidth(self.sel_exp.sizePolicy().hasHeightForWidth())
        self.sel_exp.setSizePolicy(sizePolicy2)

        self.verticalLayout_9.addWidget(self.sel_exp)

        self.box_exp = QGroupBox(self.toolBoxPage7)
        self.box_exp.setObjectName(u"box_exp")
        sizePolicy2.setHeightForWidth(self.box_exp.sizePolicy().hasHeightForWidth())
        self.box_exp.setSizePolicy(sizePolicy2)

        self.verticalLayout_9.addWidget(self.box_exp)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.previewButton = QPushButton(self.toolBoxPage7)
        self.previewButton.setObjectName(u"previewButton")

        self.horizontalLayout_5.addWidget(self.previewButton)

        self.exportButton = QPushButton(self.toolBoxPage7)
        self.exportButton.setObjectName(u"exportButton")

        self.horizontalLayout_5.addWidget(self.exportButton)


        self.verticalLayout_9.addLayout(self.horizontalLayout_5)

        self.verticalSpacer_6 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_9.addItem(self.verticalSpacer_6)

        self.toolBox.addItem(self.toolBoxPage7, u"Export")
        self.splitter.addWidget(self.toolBox)
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.gridLayout = QGridLayout(self.layoutWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.g_fz_all = PlotWidget(self.layoutWidget)
        self.g_fz_all.setObjectName(u"g_fz_all")

        self.gridLayout.addWidget(self.g_fz_all, 0, 0, 1, 1)

        self.g_fizi_all = PlotWidget(self.layoutWidget)
        self.g_fizi_all.setObjectName(u"g_fizi_all")

        self.gridLayout.addWidget(self.g_fizi_all, 0, 1, 1, 1)

        self.g_eze_all = PlotWidget(self.layoutWidget)
        self.g_eze_all.setObjectName(u"g_eze_all")
        self.g_eze_all.setEnabled(True)
        font = QFont()
        font.setBold(True)
        self.g_eze_all.setFont(font)
        self.g_eze_all.setAcceptDrops(True)
        self.g_eze_all.setInteractive(True)

        self.gridLayout.addWidget(self.g_eze_all, 0, 2, 1, 1)

        self.g_scatter1 = PlotWidget(self.layoutWidget)
        self.g_scatter1.setObjectName(u"g_scatter1")
        self.g_scatter1.setEnabled(True)
        sizePolicy.setHeightForWidth(self.g_scatter1.sizePolicy().hasHeightForWidth())
        self.g_scatter1.setSizePolicy(sizePolicy)
        self.g_scatter1.setLineWidth(0)
        self.g_scatter1.setMidLineWidth(0)
        self.g_scatter1.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.g_scatter1, 0, 3, 1, 1)

        self.g_fz_single = PlotWidget(self.layoutWidget)
        self.g_fz_single.setObjectName(u"g_fz_single")

        self.gridLayout.addWidget(self.g_fz_single, 1, 0, 1, 1)

        self.g_fizi_single = PlotWidget(self.layoutWidget)
        self.g_fizi_single.setObjectName(u"g_fizi_single")
        self.g_fizi_single.setEnabled(True)
        self.g_fizi_single.setInteractive(True)

        self.gridLayout.addWidget(self.g_fizi_single, 1, 1, 1, 1)

        self.g_eze_single = PlotWidget(self.layoutWidget)
        self.g_eze_single.setObjectName(u"g_eze_single")
        self.g_eze_single.setEnabled(True)

        self.gridLayout.addWidget(self.g_eze_single, 1, 2, 1, 1)

        self.g_scatter2 = PlotWidget(self.layoutWidget)
        self.g_scatter2.setObjectName(u"g_scatter2")
        self.g_scatter2.setEnabled(True)
        sizePolicy.setHeightForWidth(self.g_scatter2.sizePolicy().hasHeightForWidth())
        self.g_scatter2.setSizePolicy(sizePolicy)
        self.g_scatter2.setLineWidth(0)
        self.g_scatter2.setMidLineWidth(0)
        self.g_scatter2.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.g_scatter2, 1, 3, 1, 1)

        self.splitter.addWidget(self.layoutWidget)

        self.verticalLayout_10.addWidget(self.splitter)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy4)

        self.verticalLayout_4.addWidget(self.label)

        self.slid_cv = QSlider(self.centralwidget)
        self.slid_cv.setObjectName(u"slid_cv")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.slid_cv.sizePolicy().hasHeightForWidth())
        self.slid_cv.setSizePolicy(sizePolicy5)
        self.slid_cv.setOrientation(Qt.Horizontal)

        self.verticalLayout_4.addWidget(self.slid_cv)


        self.horizontalLayout_4.addLayout(self.verticalLayout_4)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setObjectName(u"label_2")
        sizePolicy4.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy4)

        self.verticalLayout_5.addWidget(self.label_2)

        self.slid_alpha = QSlider(self.centralwidget)
        self.slid_alpha.setObjectName(u"slid_alpha")
        sizePolicy4.setHeightForWidth(self.slid_alpha.sizePolicy().hasHeightForWidth())
        self.slid_alpha.setSizePolicy(sizePolicy4)
        self.slid_alpha.setMaximum(255)
        self.slid_alpha.setSingleStep(1)
        self.slid_alpha.setValue(100)
        self.slid_alpha.setOrientation(Qt.Horizontal)

        self.verticalLayout_5.addWidget(self.slid_alpha)


        self.horizontalLayout_4.addLayout(self.verticalLayout_5)

        self.delcurve = QPushButton(self.centralwidget)
        self.delcurve.setObjectName(u"delcurve")
        sizePolicy3.setHeightForWidth(self.delcurve.sizePolicy().hasHeightForWidth())
        self.delcurve.setSizePolicy(sizePolicy3)

        self.horizontalLayout_4.addWidget(self.delcurve)

        self.horizontalLayout_4.setStretch(0, 3)
        self.horizontalLayout_4.setStretch(1, 3)

        self.verticalLayout_10.addLayout(self.horizontalLayout_4)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tabfilters.setCurrentIndex(-1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"SoftMech2025", None))
        self.b_load.setText(QCoreApplication.translate("MainWindow", u"Load experiment", None))
        self.updateexperiment.setText(QCoreApplication.translate("MainWindow", u"Update HDF5", None))
        self.consolle.setText(QCoreApplication.translate("MainWindow", u"Consolle", None))
        self.b_protocol.setText(QCoreApplication.translate("MainWindow", u"Load protocol", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.toolBoxPage1), QCoreApplication.translate("MainWindow", u"Load", None))
        self.sel_filter.setItemText(0, QCoreApplication.translate("MainWindow", u"-- add --", None))

        self.toolBox.setItemText(self.toolBox.indexOf(self.toolBoxPage2), QCoreApplication.translate("MainWindow", u"Filters", None))
        self.sel_cp.setItemText(0, QCoreApplication.translate("MainWindow", u"-- none --", None))

        self.setZeroForce.setText(QCoreApplication.translate("MainWindow", u"Set CP force to 0", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.toolBoxPage3), QCoreApplication.translate("MainWindow", u"Contact point", None))
        self.sel_fmodel.setItemText(0, QCoreApplication.translate("MainWindow", u"-- none --", None))

        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Min ind [nm]", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Max ind [nm]", None))
        self.f_params.setTitle(QCoreApplication.translate("MainWindow", u"View params", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.toolBoxPage4), QCoreApplication.translate("MainWindow", u"Force model", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"Interpolate", None))
        self.es_interpolate.setText("")
        self.label_21.setText(QCoreApplication.translate("MainWindow", u"Order", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"Window", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.toolBoxPage5), QCoreApplication.translate("MainWindow", u"Elasticity spectra", None))
        self.sel_emodel.setItemText(0, QCoreApplication.translate("MainWindow", u"-- none --", None))

        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Min ind [nm]", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"Max ind [nm]", None))
        self.e_params.setTitle(QCoreApplication.translate("MainWindow", u"View params", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.toolBoxPage6), QCoreApplication.translate("MainWindow", u"Elasticity Model", None))
        self.sel_exp.setItemText(0, QCoreApplication.translate("MainWindow", u"-- none --", None))

        self.previewButton.setText(QCoreApplication.translate("MainWindow", u"Preview", None))
        self.exportButton.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.toolBoxPage7), QCoreApplication.translate("MainWindow", u"Export", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Slide through curves", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Transparency ", None))
        self.delcurve.setText(QCoreApplication.translate("MainWindow", u"Delete selected", None))
    # retranslateUi

