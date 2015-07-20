# -*- coding: utf-8 -*-
from PyQt4.QtCore import QObject, SIGNAL, QVariant
from PyQt4.QtGui import QDialog, QColorDialog, QMessageBox
from PyQt4 import uic
import os.path

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'lpConfigPlotDialog.ui'))


class LPConfigPlotDialog(QDialog, FORM_CLASS):

    def __init__(self, iface, model, index):
        super(LPConfigPlotDialog, self).__init__(None)
        self.iface = iface
        self.setupUi(self)
        self.model = model
        self.index = index
        self.data = {}
        self.row = self.model.itemFromIndex(self.index).row()
        QObject.connect(self.plotColor, SIGNAL("clicked()"),
                        self.changePlotColor)

        self.setParams()
        QObject.connect(self.CBX_Data, SIGNAL("currentIndexChanged(QString)"),
                        self.changeDataName)
        QObject.connect(self.CKB_MovAve, SIGNAL("stateChanged(int)"),
                        self.changeMovAveState)
        QObject.connect(self.SPN_MovAveN, SIGNAL("editingFinished()"),
                        self.changeMovAveN)
        QObject.connect(self.CKB_FullRes, SIGNAL("stateChanged(int)"),
                        self.changeFullResState)
        QObject.connect(self.SPN_MaxDist, SIGNAL("editingFinished()"),
                        self.changeMaxDist)
        QObject.connect(self.BTN_Remove, SIGNAL("clicked()"), self.removeData)
        QObject.connect(self.GRP_Main, SIGNAL("clicked(bool)"),
                        self.changeVisibleState)


    def setBGColor(self, target, color):
        target.setStyleSheet("background-color: %s" % color.name())

    def changeVisibleState(self, state):
        self.model.setCheckState(self.row, int(state) * 2)

    def changePlotColor(self):
        curColor = self.model.getColor(self.row)
        newColor = QColorDialog().getColor(curColor)
        if newColor.isValid() and newColor.name() is not curColor.name():
            self.model.setColor(self.row, newColor)
            self.setBGColor(self.plotColor, newColor)

    def changeDataName(self, selectedText):
        self.model.setDataName(self.row, selectedText)

    def changeMovAveState(self, state):
        self.model.setConfigs(self.row, {'movingAverage': state})

    def changeMovAveN(self):
        self.model.setConfigs(self.row, 
                              {'movingAverageN': self.SPN_MovAveN.value()})

    def changeFullResState(self, state):
        self.model.setConfigs(self.row, {'fullRes': state})

    def changeMaxDist(self):
        sameLayers = self.model.findSameLayers(self.model.getLayerId(self.row))
        config = {'maxDistance': self.SPN_MaxDist.value()}
        [self.model.setConfigs(r, config) for r in sameLayers]

    def setParams(self):
        r = self.row
        # set layer name with layer type
        layerName = self.model.getLayer(r)
        self.layerName.setText(layerName)
        self.layerType.setText(self.model.getLayerTypeName(r))
        # set display state
        self.GRP_Main.setChecked(self.model.getCheckState(r))

        # set plot color
        self.setBGColor(self.plotColor, self.model.getColor(r))

        # set data name and list
        self.setComboBoxItems(self.CBX_Data, self.model.getLayerId(r))

        # set moving average
        config = self.model.getConfigs(r)
        self.CKB_MovAve.setCheckState(config['movingAverage'])
        self.SPN_MovAveN.setValue(config['movingAverageN'])
        # set full resolution
        self.CKB_FullRes.setCheckState(config['fullRes'])

        # set max distance
        self.SPN_MaxDist.setValue(config['maxDistance'])

        # Vector vs. Raster
        if self.model.getLayerType(r):  # Raster
            self.GRP_Raster.setEnabled(True)
            self.GRP_Vector.setEnabled(False)
            self.CKB_MovAve.setEnabled(True)
            self.SPN_MovAveN.setEnabled(True)
            self.SPN_MaxDist.setEnabled(False)
        else:  # Vector
            self.GRP_Raster.setEnabled(False)
            self.GRP_Vector.setEnabled(True)
            self.CKB_MovAve.setEnabled(False)
            self.SPN_MovAveN.setEnabled(False)
            self.SPN_MaxDist.setEnabled(True)

    def setComboBoxItems(self, cmbBox, layerId):
        layers = self.iface.mapCanvas().layers()
        if len(layers) is 0:
            return
        layer = [l for l in layers if l.id() == layerId][0]
        currentData = self.model.getDataName(self.row)
        if layer.type() == layer.RasterLayer:  # Raster Layer
            [cmbBox.addItem('Band ' + str(i + 1)) 
                for i in xrange(layer.bandCount())]
        elif layer.type() == layer.VectorLayer:  # Vector Layer
            fields = layer.dataProvider().fields()
            myList = [f.name() for f in fields if f.type() == 2 or f.type() == 6]
            cmbBox.addItems(myList)
        else:
            return False

        return cmbBox.setCurrentIndex(cmbBox.findText(currentData))

    def removeData(self):
        res = QMessageBox.warning(self, 'Remove Data',
                                  'Are you sure to remove this data?',
                                  'OK', 'Cancel')
        if res is 0:  # hit OK
            self.model.removeRows(self.row, 1)
            self.close()

    def accept(self):
        self.close()

