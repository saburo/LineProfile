# -*- coding: utf-8 -*-
from PyQt4.QtCore import QPoint, Qt, SIGNAL
from PyQt4.QtGui import QColor
from qgis.core import QgsPoint, QGis
from qgis.gui import QgsMapTool, QgsRubberBand, QgsVertexMarker


class ProfileLineTool(QgsMapTool):

    def __init__(self, canvas, toolbarBtn):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.toolbarBtn = toolbarBtn
        self.terminated = True
        self.rb = QgsRubberBand(canvas, True)  # False = not a polygon
        self.rb.setWidth(2)
        self.rb.setColor(QColor(255, 20, 20, 250))
        self.rb.setIcon(QgsRubberBand.ICON_CIRCLE)

        self.rbR = QgsRubberBand(canvas, True)  # False = not a polygon
        self.rbR.setWidth(2)
        self.rbR.setColor(QColor(255, 20, 20, 150))
        self.rbR.setIcon(QgsRubberBand.ICON_CIRCLE)

        self.tieLines = []
        self.vertices = []
        self.rasterPoint = []
        self.samplingRange = []


    def canvasPressEvent(self, event):
        pt = self.toMapCoordinates(QPoint(event.pos().x(), event.pos().y()))
        if event.button() == Qt.RightButton:
            if self.terminated is False:
                self.terminated = True
                self.addVertex(pt, True)
                self.emit(SIGNAL('proflineterminated'), {'dummm', 'mmmmy'})
                return
        if self.terminated is True:
            self.resetProfileLine()
        self.rb.addPoint(pt, True)
        self.addVertex(pt)

    def updateProfileLine(self):
        pt = self.getProfPoints()
        self.rb.reset()
        self.resetVertices()
        ptLast = pt.pop()
        for p in pt:
            point = QgsPoint(p[0], p[1])
            self.rb.addPoint(point, True)
            self.addVertex(point)
        point = QgsPoint(ptLast[0], ptLast[1])
        self.rb.addPoint(point, True)
        self.addVertex(point, True)
        self.terminated = True

    def canvasMoveEvent(self, event):
        if self.terminated is False:
            plen = self.rb.numberOfVertices()
            if plen > 0:
                pt = self.toMapCoordinates(
                    QPoint(event.pos().x(), event.pos().y()))
                self.rb.movePoint(plen - 1, pt)

    def canvasReleaseEvent(self, event):
        pass

    def canvasDoubleClickEvent(self, event):
        self.emit(SIGNAL('doubleClicked'))
        self.resetProfileLine()

    def getProfPoints(self):
        # [[x0, y0], [x1, y1], [x2, y2],. ., [xn, yn]]
        n = self.rb.numberOfVertices()
        profVertices = []
        for i in xrange(n):
            pt = self.rb.getPoint(0, i)
            profVertices.append([pt.x(), pt.y()])
        return profVertices

    def resetProfileLine(self):
        self.rb.reset()
        self.rbR.reset()
        self.resetTieLies()
        self.resetVertices()
        self.resetRasterPoints()
        self.resetSamplingRange()
        self.terminated = False

    def drawTieLine(self, pt1, pt2):
        tl = QgsRubberBand(self.canvas, True)
        tl.setWidth(1)
        tl.setColor(QColor(255, 255, 100, 200))
        tl.addPoint(QgsPoint(pt1[0], pt1[1]), True)
        tl.addPoint(QgsPoint(pt2[0], pt2[1]), True)
        self.tieLines.append(tl)

    def resetTieLies(self):
        [tl.reset() for tl in self.tieLines]
        [self.canvas.scene().removeItem(tl) for tl in self.tieLines]
        self.tieLines = []

    def addVertex2(self, pt1):
        tl = QgsRubberBand(self.canvas, QGis.Point)
        tl.setIconSize(5)
        tl.setIcon(QgsRubberBand.ICON_CIRCLE)
        tl.setColor(QColor(255, 255, 255, 200))
        tl.addPoint(QgsPoint(pt1[0], pt1[1]), True)
        self.rasterPoint.append(tl)

    def addSamplingRange(self, pt1, terminator=False):
        if terminator:
            icon = QgsRubberBand.ICON_FULL_BOX
        else:
            icon = QgsRubberBand.ICON_CIRCLE
        tl = QgsRubberBand(self.canvas, QGis.Point)
        tl.setIconSize(3)
        # tl.setWidth(5)
        tl.setIcon(icon)
        tl.setColor(QColor(255, 255, 220, 200))
        tl.addPoint(QgsPoint(pt1[0], pt1[1]), True)
        self.samplingRange.append(tl)

    def addSamplingArea(self, pts, color):
        myColor = QColor(color)
        myColor.setAlpha(35)
        for pt in pts:
            rb = QgsRubberBand(self.canvas, QGis.Polygon)
            rb.addPoint(QgsPoint(pt[0][0], pt[0][1]))
            rb.addPoint(QgsPoint(pt[1][0], pt[1][1]))
            rb.addPoint(QgsPoint(pt[3][0], pt[3][1]))
            rb.addPoint(QgsPoint(pt[2][0], pt[2][1]))
            rb.addPoint(QgsPoint(pt[0][0], pt[0][1]))
            rb.setColor(myColor)
            rb.setWidth(2)
            # rb.show()
            self.samplingRange.append(rb)


    def addSamplingRange2(self, pts, color):
        myColor = QColor(color)
        myColor.setAlpha(200)
        mySize = 3
        for pt1 in pts:
            qpt = QgsPoint(pt1[0], pt1[1])
            # tl.addPoint(qpt, True)
            tl2 = QgsRubberBand(self.canvas, QGis.Point)
            tl2.addPoint(qpt, True)
            tl2.setIconSize(mySize)
            tl2.setIcon(QgsRubberBand.ICON_CIRCLE)
            tl2.setColor(myColor)
            self.samplingRange.append(tl2)
            # vt = QgsVertexMarker(self.canvas)
            # vt.setIconType(QgsVertexMarker.ICON_BOX)
            # vt.setIconSize(2)
            # vt.setColor(QColor(255, 0, 220, 200))
            # vt.setCenter(qpt) 
            # self.samplingRange.append(vt)
        # self.samplingRange.append(tl)

    def drawSamplingLine(self, lineWidth=3):
        self.rbR.reset()
        self.rbR.setWidth(lineWidth)
        print self.rbR
        for i in xrange(self.rb.numberOfVertices()):
            pt = self.rb.getPoint(0, i)
            print pt
            self.rbR.addPoint(pt, True)

    def addVertex(self, pt1, terminator=False):
        if terminator:
            icon = QgsRubberBand.ICON_FULL_BOX
        else:
            icon = QgsRubberBand.ICON_CIRCLE
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
        [tl.reset() for tl in self.vertices]
        [self.canvas.scene().removeItem(tl) for tl in self.vertices]
        self.vertices = []

    def resetRasterPoints(self):
        [tl.reset() for tl in self.rasterPoint]
        [self.canvas.scene().removeItem(tl) for tl in self.rasterPoint]
        self.rasterPoint = []

    def resetSamplingRange(self):
        [tl.reset() for tl in self.samplingRange]
        [self.canvas.scene().removeItem(tl) for tl in self.samplingRange]
        self.samplingRange = []

    # def activate(self):
    #     self.toolbarBtn.setCheckable(True)
    #     self.toolbarBtn.setChecked(True)
    #     QgsMapTool.activate(self)

    # def deactivate(self):
    #     QgsMapTool.deactivate(self)
    #     self.toolbarBtn.setCheckable(False)
        # self.resetProfileLine()
        # print 'signal emitting (deactivate)'
        # self.emit(SIGNAL('deactivate'))
