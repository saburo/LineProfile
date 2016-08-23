# -*- coding: utf-8 -*-
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QStandardItemModel, QBrush, QStandardItem, QColor, \
    QIcon


class MyTableViewModel(QStandardItemModel):
    """docstring for MyTableViewModel"""

    updateFlag = False

    def __init__(self):
        super(MyTableViewModel, self).__init__()
        self.c = {
            'state':      0,
            'color':      1,
            'layer':      2,
            'data':       3,
            'config':     4,
            'layerId':    5,
            'layerType':  6,
        }
        self.n = len(self.c)
        [self.insertColumn(i) for i in xrange(self.n)]
        self.setHorizontalHeaderLabels(['', '', 'Layer', 'Data', ''])

        self.movAveDefault = 10
        self.maxDistDefault = 100.00
        self.lineWidthDefault = 1

    """""""""""""""""""""""""""""""""""""""
    * Methods
    """""""""""""""""""""""""""""""""""""""
    def addElement(self, layer, element):
        myColor = self.getAvailableColor()
        iconPath = ':/plugins/LineProfile/img/alg.png'
        newRow = [QStandardItem() for n in xrange(self.n)]

        newRow[self.c['state']].setCheckable(True)
        newRow[self.c['state']].setCheckState(Qt.Checked)
        newRow[self.c['color']].setBackground(QBrush(myColor))
        newRow[self.c['color']].setToolTip(myColor.name())
        newRow[self.c['layer']].setText(layer.name())
        newRow[self.c['layer']].setToolTip(layer.name())
        newRow[self.c['data']].setText(element)
        newRow[self.c['data']].setToolTip(element)
        newRow[self.c['layerId']].setText(str(layer.id()))
        newRow[self.c['layerType']].setText(str(layer.type()))

        sameLayer = self.findSameLayers(str(layer.id()))
        if sameLayer:
            mDist = self.getConfigs(sameLayer[0])['maxDistance']
        else:
            mDist = self.maxDistDefault

        newRow[self.c['config']].setIcon(QIcon(iconPath))
        newRow[self.c['config']].setToolTip('config')
        config = {
            'movingAverage': Qt.Unchecked,           # int
            'movingAverageN': self.movAveDefault,     # int
            'maxDistance': mDist,                  # float
            'lineWidth': self.lineWidthDefault,  # float
            'fullRes': Qt.Unchecked,           # int
        }
        newRow[self.c['config']].setData(config)
        self.appendRow(newRow)
        return self.rowCount() - 1

    def getAvailableColor(self):
        myColors = [
            QColor(0, 160, 191, 255),
            QColor(208, 33, 43, 255),
            QColor(166, 192, 125, 255),
            QColor(249, 144, 69, 255),
            QColor(240, 205, 96, 255),
            QColor(255, 0, 0, 255),     # red
            QColor(0, 0, 255, 255),     # blue
            QColor(0, 255, 50, 255),    # green
            QColor(255, 50, 255, 255),  # magenta
            QColor(50, 255, 255, 255),  # cyan
            QColor(255, 255, 0, 255),   # yellow
        ]
        usedColors = []
        for r in xrange(self.rowCount()):
            cColor = self.getColor(r)
            if cColor in myColors:
                usedColors.append(myColors.index(cColor))
        usedColors = list(set(usedColors))
        if len(usedColors) is 0 or len(usedColors) is len(myColors):
            return myColors[0]
        for i in xrange(len(myColors)):
            if i not in usedColors:
                return myColors[i]

    def getColumnIndex(self, colName):
        return self.c[colName]

    def getColulmnNames(self):
        return self.c.keys()

    def findSameLayers(self, layerId):
        sameLayers = self.findItems(layerId, Qt.MatchExactly,
                                    self.c['layerId'])
        return [l.row() for l in sameLayers]

    """""""""""""""""""""""""""""""""""""""
    * GETTERS
    """""""""""""""""""""""""""""""""""""""

    def getCheckState(self, row):
        return self.item(row, self.c['state']).checkState()

    def getColorName(self, row):
        return self.getColor(row).name()

    def getColor(self, row):
        return self.item(row, self.c['color']).background().color()

    def getDataName(self, row):
        return self.item(row, self.c['data']).text()

    def getLayer(self, row):
        return self.item(row, self.c['layer']).text()

    def getLayerId(self, row):
        return self.item(row, self.c['layerId']).text()

    def getLayerType(self, row):
        return int(self.item(row, self.c['layerType']).text())

    def getLayerTypeName(self, row):
        return 'Raster' if self.getLayerType(row) else 'Vector'

    def getConfigs(self, row):
        return self.item(row, self.c['config']).data()

    """""""""""""""""""""""""""""""""""""""
    * SETTERS
    """""""""""""""""""""""""""""""""""""""

    def setCheckState(self, row, state):
        self.item(row, self.c['state']).setCheckState(state)

    def setColor(self, row, color):
        self.item(row, self.c['color']).setBackground(QBrush(color))

    def setDataName(self, row, name):
        self.item(row, self.c['data']).setText(name)

    def setConfigs(self, row, confDict):
        config = self.getConfigs(row)
        myUpdateFlag = False
        for param, value in confDict.iteritems():
            if param in config:
                config[param] = value
                myUpdateFlag = True
        if myUpdateFlag:
            self.item(row, self.c['config']).setData(config)