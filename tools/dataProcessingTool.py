# -*- coding: utf-8 -*-
from PyQt4.QtCore import QPyNullVariant
from math import atan, cos, sin, sqrt
from qgis.core import QgsPoint, QgsRaster


class DataProcessingTool():

    def __init__(self):
        self.tieLine = []
        self.tieLineFlag = False
        self.tieLineDone = []
        self.samplingPoints = []
        self.samplingRange = []
        self.samplingArea = []
        self.samplingWidth = 0

    def getProfileLines(self, profilePoints):
        out = []
        for i in xrange(len(profilePoints) - 1):
            pt1 = profilePoints[i]
            pt2 = profilePoints[i + 1]
            a, b = self.calcSlopeIntercept(pt1, pt2)
            out.append({
                's': pt1,  # [x, y] start
                'e': pt2,  # [x, y] end
                'a': a,    # slope
                'b': b,    # intercept
                'd': self.getDistance(pt1, pt2)
            })
        return out

    def getVectorProfile(self, pLines, layer, field,
                         distLimit=1000000, distanceField=None, pIndex=0):
        x = []
        y = []
        d = 0
        if layer.selectedFeatureCount() > 0:
            featuresForPlot = layer.selectedFeatures()
        else:
            featuresForPlot = layer.getFeatures()

        if distanceField is not None:
            layer.startEditing()

        lid = layer.id()

        while len(self.tieLine) <= pIndex:
            self.tieLine.append([])
            self.tieLineDone.append([])

        if lid not in self.tieLineDone[pIndex]:
            tieLineFlag = True
            self.tieLineDone[pIndex].append(lid)
        else:
            tieLineFlag = False

        for f in featuresForPlot:
            # calc coordinates of intercept between normal line and profile
            # line
            if type(f.attribute(field)) is type(QPyNullVariant(int)):
                continue
            pt = f.geometry().asPoint()
            if distanceField is not None:
                prjPoint = self.getProjectedPoint(pLines, pt, distLimit, pIndex)
            else:
                prjPoint = self.getProjectedPoint(pLines, pt, distLimit) 

            if prjPoint is not False:
                d = self.sumD(pLines[:prjPoint[2]])
                d += self.getDistance([prjPoint[0], prjPoint[1]],
                                      pLines[prjPoint[2]]['s'])
                x.append(d)
                y.append(f.attribute(field))

                if tieLineFlag:
                    self.addTieLine(pIndex, list(pt), prjPoint[:2])

                if distanceField is not None:
                    f[distanceField] = d
                    layer.updateFeature(f)

        if distanceField is not None:
            layer.commitChanges()
        x, y = self.sortDataByX(x, y)

        return [x, y]

    def sortDataByX(self, x, y):
        sorted_x = list(x)
        sorted_y = []
        sorted_x.sort()
        for i in sorted_x:
            idx = x.index(i)
            sorted_y.append(y[idx])
            x[idx] = None
        return sorted_x, sorted_y

    def sumD(self, pLines):
        return reduce(lambda x, y: x + y['d'], pLines, 0.0)

    def getCurrentCoordinates(self, pLines, dist):
        d = 0.0
        for k, v in enumerate(pLines):
            d += v['d']
            if dist < d:
                dist -= d - v['d']
                break
        cu = pLines[k]
        if cu['a'] == float('inf'):  # vertical
            dX = 0
            dY = dist
        else:
            dX = cos(atan(cu['a'])) * dist
            dY = cu['a'] * dX
        # +/- direction
        tmp = 1 if cu['e'][1] > cu['s'][1] else -1
        xDirection = 1 if cu['e'][0] > cu['s'][0] else -1
        yDirection = tmp if cu['a'] >= 0 else tmp * -1
        x = cu['s'][0] + xDirection * dX
        y = cu['s'][1] + yDirection * dY

        return [x, y]

    def getRasterProfile(self, pLines, layer, band, fullRes, equiWidth=0):
        x = []
        y = []
        self.initSamplingPoints()
        self.initSamplingRange()
        self.initSamplingArea()

        dp = layer.dataProvider()
        band = int(band.replace('Band ', ''))
        pixelSize = layer.rasterUnitsPerPixelX() if fullRes else 1
        cP = 0  # index number of current segment
        tmpD = 0  # current distance within current segment
        totalD = self.sumD(pLines)  # total distance of profile line
        # max distance of current segment
        tmpDMax = self.sumD(pLines[0:cP + 1])
        tmpX, tmpY = pLines[cP]['s']
        equiWidth = int(round(equiWidth / 2 / pixelSize))
        self.setSamplingWidth(equiWidth)
        acP = -1
        while tmpD < totalD:
            # first point of each segment
            if tmpD >= tmpDMax or tmpD == 0:
                if tmpD > 0:
                    cP += 1
                    tmpD = tmpDMax
                    tmpX = pLines[cP]['s'][0]
                    tmpY = pLines[cP]['s'][1]
                    tmpDMax = self.sumD(pLines[0:cP + 1])

                slope, direction = self.getDirectionSlope(pLines[cP])
                if slope is False:  # vertical
                    dX = 0
                    dY = 1
                    if pLines[cP]['s'][1] > pLines[cP]['e'][1]:
                        dY = -1
                else:
                    dX = abs(cos(atan(pLines[cP]['a']))) * direction
                    dY = abs(sin(atan(pLines[cP]['a']))) * direction * slope

                # scale by pixel size of raster layer
                dX *= pixelSize
                dY *= pixelSize

            # qgsPoint
            # find equilevel
            # get equilevel points => equiPoints
            if acP is not cP:
                acP = cP
                # start point
                acP_s = self.getEquiPoints(pLines[acP]['s'][0], pLines[
                                           acP]['s'][1], equiWidth, dX, dY)
                # end point
                acP_e = self.getEquiPoints(pLines[acP]['e'][0], pLines[
                                           acP]['e'][1], equiWidth, dX, dY)
                self.addSamplingArea(
                    [acP_s[0], acP_s[-1], acP_e[0], acP_e[-1]])
            equiPoints = self.getEquiPoints(tmpX, tmpY, equiWidth, dX, dY)
            # qgsPoint[i] = QgsPoint(equiPoints[i].X, equiPoints[i].Y)
            tmpVal = 0

            self.addSamplingRange(equiPoints)
            for n in xrange(0, len(equiPoints)):
                # tmpVal += self.getPointValue(dp, qgsPoint[i], band)
                qgsPoint = QgsPoint(equiPoints[n][0], equiPoints[n][1])
                tmpVal += self.getPointValue(dp, qgsPoint, band)

            aveVal = tmpVal / len(equiPoints)
            # averageVal = tmpVal / length(equiPoints)
            # y.append(tmpVal / len(equiPoints)) # add averaged value
            # qgsPoint = QgsPoint(tmpX, tmpY)
            # y.append(self.getPointValue(dp, qgsPoint, band))
            y.append(aveVal)
            x.append(tmpD)
            self.samplingPoints.append(QgsPoint(tmpX, tmpY))
            tmpX += dX
            tmpY += dY
            tmpD += pixelSize
        else:
            endPoint = pLines[len(pLines) - 1]['e']
            # qgsPoint = QgsPoint(tmpX, tmpY)
            equiPoints = self.getEquiPoints(
                endPoint[0], endPoint[1], equiWidth, dX, dY)
            tmpVal = 0
            self.addSamplingRange(equiPoints)
            for n in xrange(0, len(equiPoints)):
                qgsPoint = QgsPoint(equiPoints[n][0], equiPoints[n][1])
                tmpVal += self.getPointValue(dp, qgsPoint, band)
            aveVal = tmpVal / len(equiPoints)
            y.append(aveVal)
            # y.append(self.getPointValue(dp, qgsPoint, band))
            x.append(totalD)
            # self.samplingPoints.append(qgsPoint)
            self.samplingPoints.append(endPoint)
        return [x, y]

    def getEquiPoints(self, x, y, w, dx, dy):
        out = []
        if w < 1:
            out = [[x, y]]
        else:
            rdx = dy
            rdy = -dx
            for i in xrange(-w, w + 1):
                out.append([x + i * rdx, y + i * rdy])
        return out

    def getPointValue(self, dp, point, band):
        res = dp.identify(point, QgsRaster.IdentifyFormatValue).results()
        return res[band] if res[band] is not None else 0

    def getProjectedPoint(self, pLines, pt, distLimit, pIndex=None):
        minDist = 1.0E+12
        tmpDist = 0.0
        x = None  # coordinate x
        y = None  # coordinate y
        i = 0
        for index, pLine in enumerate(pLines):  
            slope = pLine['a']
            intercept = pLine['b']
            if slope == float('inf'):  # vertical profile line
                tmpx = pLine['e'][0]
                tmpy = pt[1]
            elif slope == 0:  # horizontal profile line
                tmpx = pt[1]
                tmpy = pLine['e'][1]
            elif pt[1] == slope * pt[0] + intercept:  # point on profile line
                tmpx = pt[0]
                tmpy = pt[1]
            else:  # others
                a = -1 / slope
                b = pt[1] - (a * pt[0])
                tmpx = (b - intercept) / (slope - a)
                tmpy = a * tmpx + b
            # a, b = self.calcNormalLine(pt, slope, intercept)
            # if a == float('inf'):
            #     # normal line = vertical line
            #     tmpx = pt[1]
            #     tmpy = pLine['e'][1]
            # elif a == 0:
            #     # normal line = horizontal
            #     tmpx = pLine['e'][0]
            #     tmpy = pt[1]
            # elif pt[1] == slope * pt[0] + intercept:
            #     tmpx = pt[0]
            #     tmpy = pt[1]
            # else:
            #     tmpx = (b - intercept) / (slope - a)
            #     tmpy = a * tmpx + b

            tmpDist = self.getDistance(pt, [tmpx, tmpy])

            if self.isPointOnProfilefLine(tmpx, tmpy, pLine):
                if minDist > tmpDist:
                    minDist = tmpDist
                    x = tmpx
                    y = tmpy
                    i = index

        # check vertices
        cV = self.getClosestVertex(pLines, pt)

        if x is None and cV['seg'] == -1:
            return False

        if x is None and cV['seg'] > -1:
            # vertex is the projected point
            i = cV['seg']
            minDist = cV['d']
            x, y = pLines[i]['e']
        elif x is not None and cV['seg'] > -1:
            if cV['d'] < minDist:
                # vertex is closer than normal line
                i = cV['seg']
                x, y = pLines[i]['e']

        if minDist > distLimit:
            return False

        return [x, y, i]

    def isPointOnProfilefLine(self, x, y, pLine):
        if pLine['s'][0] < pLine['e'][0]:
            lx = pLine['s'][0]
            hx = pLine['e'][0]
        else:
            lx = pLine['e'][0]
            hx = pLine['s'][0]
        if pLine['s'][1] < pLine['e'][1]:
            ly = pLine['s'][1]
            hy = pLine['e'][1]
        else:
            ly = pLine['e'][1]
            hy = pLine['s'][1]
        if lx <= x <= hx and ly <= y <= hy:
            return True
        return False

    def getClosestVertex(self, pLines, pt, pIndex=None):
        d = 1.0E+12
        segment = 0
        # First and last vertices shouldn't be the closest vertex.
        for index, pLine in enumerate(pLines):
            if pIndex is not None and index != pIndex:
                continue
            if index == 0:
                tmpD = self.getDistance(pLine['e'], pt)
                # excluding first vertex
                if self.getDistance(pLine['s'], pt) < tmpD:
                    return {'seg': -1}
            else:
                tmpD = self.getDistance(pLine['e'], pt)
            if d > tmpD:
                d = tmpD
                segment = index
        # excluding last vertex
        if segment == len(pLines) - 1:
            return {'seg': -1}

        return {'seg': segment, 'd': d}

    def calcNormalLine(self, pt, slope, intercept):
        x, y = pt
        if slope == 0 and intercept == 0:
            # profile line is vertical line
            # get horizontal line
            a = 0
            b = y
        elif slope == 0:
            # profile line is horizontal line
            # get vertical line
            a = float('inf')
            b = None
        else:
            a = -1 / slope
            b = y - (a * x)
        return [a, b]

    def calcSlopeIntercept(self, pt1, pt2):
        # a: slope, b: intercept
        if pt1[0] == pt2[0] and pt1[1] == pt2[1]:  # identical
            a = None
            b = None
        elif pt2[1] == pt1[1]:  # horizontal
            a = 0
            b = pt2[1]
        elif pt2[0] == pt1[0]:  # vertical
            a = float('inf')
            b = None
        else:
            a = (pt2[1] - pt1[1]) / (pt2[0] - pt1[0])
            b = pt2[1] - a * pt2[0]
        return [a, b]

    def getDistance(self, pt1, pt2):
        return sqrt((pt2[0] - pt1[0])**2 + (pt2[1] - pt1[1])**2)

    def initTieLines(self):
        self.tieLine = []
        self.tieLineFlag = False
        self.tieLineDone = []

    def addTieLine(self, pIndex, pt1, pt2):
        self.tieLine[pIndex].append([pt1, pt2])

    def getTieLines(self):
        return self.tieLine

    def initSamplingPoints(self):
        self.samplingPoints = []

    def getSamplingPoints(self):
        return self.samplingPoints

    def initSamplingRange(self):
        self.samplingRange = []

    def initSamplingArea(self):
        self.samplingArea = []

    def addSamplingRange(self, point):
        self.samplingRange.append(point)

    def addSamplingArea(self, myList):
        self.samplingArea.append(myList)

    def getSamplingRange(self):
        return self.samplingRange

    def getSamplingArea(self):
        return self.samplingArea

    def setSamplingWidth(self, width):
        self.samplingWidth = width

    def getSamplingWidth(self):
        return self.samplingWidth

    def getDirectionSlope(self, pt):
        start = pt['s']
        end = pt['e']

        if end[0] > start[0]:
            direction = 1
            if end[1] > start[1]:
                slope = 1
            elif end[1] < start[1]:
                slope = -1
            else:
                slope = 0
        elif end[0] < start[0]:
            direction = -1
            if end[1] < start[1]:
                slope = 1
            elif end[1] > start[1]:
                slope = -1
            else:
                slope = 0
        else:
            slope = False
            direction = False
        return [slope, direction]
