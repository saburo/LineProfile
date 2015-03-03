# -*- coding: utf-8 -*-
from PyQt4.QtCore import QPoint, Qt, SIGNAL
from PyQt4.QtGui import QColor
from qgis.core import QgsPoint, QGis
from qgis.gui import QgsMapTool, QgsRubberBand

class ProfileLineTool(QgsMapTool):

    def __init__(self, canvas, toolbarBtn):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.toolbarBtn =toolbarBtn
        self.terminated = True
        self.rb = QgsRubberBand(canvas, True)  # False = not a polygon
        self.rb.setWidth(4)
        self.rb.setColor(QColor(255, 100, 100, 250))
        self.rb.setIcon(QgsRubberBand.ICON_CIRCLE)

        self.tielines = []
        self.vertices = []
        self.rasterPoint = []


    def canvasPressEvent(self, event):
        pt = self.toMapCoordinates(QPoint(event.pos().x(), event.pos().y()))
        if event.button() == Qt.RightButton:
            if self.terminated == False:
                self.terminated = True
                self.addVertex(pt, True)
                self.emit(SIGNAL('proflineterminated'), {'dummm', 'mmmmy'})
                return
        if self.terminated == True:
            self.resetProfileLine()
        self.rb.addPoint(pt, True)
        self.addVertex(pt)

    def canvasMoveEvent(self, event):
        if self.terminated == False:
            plen = self.rb.numberOfVertices()
            if plen > 0:
                pt = self.toMapCoordinates(QPoint(event.pos().x(), event.pos().y()))
                self.rb.movePoint(plen - 1, pt)

    def canvasReleaseEvent(self, event):
        pass

    def canvasDoubleClickEvent(self, event):
        self.emit(SIGNAL('doubleClicked'))
        self.resetProfileLine()

    def getProfPoints(self):
        n = self.rb.numberOfVertices()
        profVertices = []
        for i in range(0, n):
            pt = self.rb.getPoint(0, i)
            profVertices.append([pt.x(), pt.y()])
        return profVertices

    def resetProfileLine(self):
        self.rb.reset()
        self.resetTieLies()
        self.resetVertices()
        self.resetRasterPoints()
        self.terminated = False


    def drawTieLine(self, pt1, pt2):
        tl = QgsRubberBand(self.canvas, True)
        tl.setWidth(1)
        tl.setColor(QColor(255, 255, 100, 200))
        tl.addPoint(QgsPoint(pt1[0], pt1[1]), True)
        tl.addPoint(QgsPoint(pt2[0], pt2[1]), True)
        self.tielines.append(tl)

    def resetTieLies(self):
        for tl in self.tielines:
            tl.reset()
        self.tielines = []

    def addVertex2(self, pt1):
        tl = QgsRubberBand(self.canvas, QGis.Point)
        tl.setIconSize(5)
        tl.setIcon(QgsRubberBand.ICON_CIRCLE)
        tl.setColor(QColor(255, 255, 255, 200))
        tl.addPoint(QgsPoint(pt1[0], pt1[1]), True)
        self.rasterPoint.append(tl)

    def addVertex(self, pt1, terminator=False):
        icon = QgsRubberBand.ICON_FULL_BOX if terminator else QgsRubberBand.ICON_CIRCLE
        tl = QgsRubberBand(self.canvas, QGis.Point)
        tl.setIconSize(10)
        # tl.setWidth(5)
        tl.setIcon(icon)
        tl.setColor(QColor(255, 100, 100, 200))
        tl.addPoint(QgsPoint(pt1[0], pt1[1]), True)
        self.vertices.append(tl)

    def drawProfileLineFromPoints(self, points):
        self.resetProfileLine()
        num = len(points)
        for i in range(0, num - 1):
            self.rb.addPoint(points[i], True)
            self.addVertex(points[i])
        self.terminated = True
        self.rb.addPoint(points[i + 1], True)
        self.addVertex(points[i + 1], True)

    def resetVertices(self):
        for tl in self.vertices:
            tl.reset()
        self.vertices = []

    def resetRasterPoints(self):
        for tl in self.rasterPoint:
            tl.reset()
        self.rasterPoint = []

    def activate(self):
        print "activate"
        self.toolbarBtn.setCheckable(True)
        self.toolbarBtn.setChecked(True)
        QgsMapTool.activate(self)

    def deactivate(self):
        QgsMapTool.deactivate(self)
        self.toolbarBtn.setCheckable(False)
        self.resetProfileLine()
        self.emit(SIGNAL('deactivate'))
