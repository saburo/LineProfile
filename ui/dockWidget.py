# -*- coding: utf-8 -*-
from PyQt4.QtCore import QObject, SIGNAL, Qt
from PyQt4.QtGui import QDockWidget
from PyQt4 import uic

import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dockWidget.ui'))


class DockWidget(QDockWidget, FORM_CLASS):

    plotWdg = None
    currentPLayer = None
    currentSLayer = None

    """docstring for DockWidget"""

    def __init__(self, parent, iface1):
        QDockWidget.__init__(self, parent)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.iface = iface1
        self.setupUi(self)

        self.layersUpdateFlag = False
        self.fieldsUpdateFlag = False

        self.Grp_SecondaryY.setChecked(False)

        QObject.connect(
            self.myLayers, SIGNAL("currentIndexChanged(int)"),
            self.myLayersChanged)
        QObject.connect(
            self.myFields, SIGNAL("currentIndexChanged(int)"),
            self.myFieldsChanged)
        QObject.connect(self.mySecondLayers, SIGNAL(
            "currentIndexChanged(int)"), self.mySecondLayersChanged)
        QObject.connect(self.mySecondFields, SIGNAL(
            "currentIndexChanged(int)"), self.mySecondFieldsChanged)
        QObject.connect(self.myExportProfileLineBtn, SIGNAL(
            "clicked(bool)"), self.mySecondFieldsChanged)

        self.updateLayerFieldComboBox()

    def closeEvent(self, event):
        self.emit(SIGNAL("closed(PyQt_PyObject)"), self)
        return QDockWidget.closeEvent(self, event)

    def showDockWidget(self):
        self.location = Qt.BottomDockWidgetArea
        self.iface.mapCanvas().setRenderFlag(False)

        # Draw the widget
        self.iface.addDockWidget(self.location, self)

        self.iface.mapCanvas().setRenderFlag(True)

    def updateLayerFieldComboBox(self):
        canvas = self.iface.mapCanvas()
        self.layersUpdateFlag = True
        self.myLayers.clear()
        self.mySecondLayers.clear()

        for l in canvas.layers():
            self.myLayers.addItem(l.name(), l.id())
            self.mySecondLayers.addItem(l.name(), l.id())

        if canvas.layerCount() > 0:
            # First Fields
            currentPLayerIndex = self.myLayers.findData(self.currentPLayer)
            if currentPLayerIndex < 0:
                currentPLayerIndex = 0
            pLayer = canvas.layer(currentPLayerIndex)
            self.currentPLayer = pLayer.id()
            self.myLayers.setCurrentIndex(currentPLayerIndex)
            self.updateFields(pLayer, self.myFields)
            # Second Fields
            currentSLayerIndex = self.mySecondLayers.findData(
                self.currentSLayer)
            if currentSLayerIndex < 0:
                currentSLayerIndex = 0
            sLayer = canvas.layer(currentSLayerIndex)
            self.currentSLayer = sLayer.id()
            self.mySecondLayers.setCurrentIndex(currentSLayerIndex)
            self.updateFields(sLayer, self.mySecondFields)
        else:
            self.myFields.clear()
            self.mySecondFields.clear()
            self.currentPLayer = None
            self.currentSLayer = None

        self.layersUpdateFlag = False
        self.emit(SIGNAL('cmboxupdated'))

    def updateFields(self, layer, targetFields):
        self.fieldsUpdateFlag = True
        targetFields.clear()
        if not layer:
            return False
        dp = layer.dataProvider()
        if layer.type():  # raster layer
            for i in range(0, layer.bandCount()):
                targetFields.addItem(layer.bandName(i + 1))
        else:  # vector layer
            fields = dp.fields()
            for f in fields:
                # numeric fields only // type: int = 2, double = 6
                if f.type() == 2 or f.type() == 6:
                    targetFields.addItem(f.name())
        self.fieldsUpdateFlag = False

    def myLayersChanged(self, index):
        if self.layersUpdateFlag:
            return False

        if index < 0:
            layer = None
        else:
            layer = self.iface.mapCanvas().layer(index)
            self.currentPLayer = layer.id()
        self.updateFields(layer, self.myFields)
        self.emit(SIGNAL('cmboxupdated'))

    def mySecondLayersChanged(self, index):
        if self.layersUpdateFlag:
            return False

        if index < 0:
            layer = None
        else:
            layer = self.iface.mapCanvas().layer(index)
            self.currentSLayer = layer.id()
        self.updateFields(layer, self.mySecondFields)
        self.emit(SIGNAL('cmboxupdated'))

    def myFieldsChanged(self, index):
        if not self.fieldsUpdateFlag:
            self.emit(SIGNAL('cmboxupdated'))

    def mySecondFieldsChanged(self, index):
        if not self.fieldsUpdateFlag:
            self.emit(SIGNAL('cmboxupdated'))
