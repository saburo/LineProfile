# -*- coding: utf-8 -*-
from math import atan, cos, sin, sqrt
from qgis.core import QgsPoint, QgsRaster

class DataProcessingTool():

    def __init__(self):
        self.tieLine = []

    def getProfileLines(self, profilePoints):
        out = []
        for i in range(0, len(profilePoints) - 1):
            pt1 = profilePoints[i]
            pt2 = profilePoints[i + 1]
            a, b = self.calcSlopeIntercept(pt1, pt2)
            out.append({
                'start': pt1,
                'end':   pt2,
                'a': a,
                'b': b,
                'd': self.getDistance(pt1, pt2)
            })
        return out

    def getVectorProfile(self, pLines, layer, field, distLimit=1000000, distanceField=None):
        x = []
        y = []
        d = 0
        if layer.selectedFeatureCount() > 0:
            featuresForPlot = layer.selectedFeatures()
        else:
            featuresForPlot = layer.getFeatures()

        if distanceField:
            layer.startEditing()

        for f in featuresForPlot:
            # calc coordinate of intercept between normal line and profile line
            pt = f.geometry().asPoint()
            prjProint = self.getProjectedPoint(pLines, pt, distLimit)
            if prjProint != False:
                d = self.sumD(pLines[:prjProint[2]])
                d += self.getDistance([prjProint[0], prjProint[1]], pLines[prjProint[2]]['start'])
                x.append(d)
                y.append(f.attribute(field))
                self.addTieLine(pt, prjProint[:2])
                if distanceField:
                    f[distanceField] = d
                    layer.updateFeature(f)

        if distanceField:
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

    def getRasterProfile(self, pLines, layer, band=1):
        x = []
        y = []
        dp = layer.dataProvider()
        band = int(band.replace('Band ', ''))
        cP = 0
        tmpD = 0
        totalD = self.sumD(pLines)
        tmpDMax = self.sumD(pLines[0:cP+1])
        tmpX, tmpY = pLines[cP]['start']
        while tmpD < totalD:
            if tmpD >= tmpDMax or tmpD == 0:
                if pLines[cP]['end'][0] > pLines[cP]['start'][0]:
                    direction = 1
                elif pLines[cP]['end'][0] == pLines[cP]['start'][0]: # vertical
                    direction = 1 if pLines[cP]['end'][1] > pLines[cP]['start'][1] else -1
                else:
                    direction = -1
                slope = 1 if pLines[cP]['a'] >= 0 else -1
                dX = abs(cos(atan(pLines[cP]['a']))) * direction if pLines[cP]['b'] != 0 else 0
                dY = abs(sin(atan(pLines[cP]['a']))) * direction * slope if pLines[cP]['b'] != 0 else 1 * direction
                if tmpD > 0:
                    tmpD = tmpDMax
                    tmpX = pLines[cP]['start'][0]
                    tmpY = pLines[cP]['start'][1]
                    tmpDMax = self.sumD(pLines[0:cP+1])
                    cP += 1
            res = dp.identify(QgsPoint(tmpX, tmpY), QgsRaster.IdentifyFormatValue).results()
            y.append(res[band])
            x.append(tmpD)
            tmpX += dX
            tmpY += dY
            tmpD += 1
        else:
            endPoint = pLines[len(pLines)-1]['end']
            res = dp.identify(QgsPoint(endPoint[0], endPoint[1]), QgsRaster.IdentifyFormatValue).results()
            y.append(res[band])
            x.append(totalD)
        return [x, y]

    def getProjectedPoint(self, pLines, pt, distLimit):
        minDist = 1E+12
        tmpDist = 0.0
        x = None # coordinate x
        y = None # coordinate y
        i = 0 #

        for index, pLine in enumerate(pLines):
            vertexDist = 1E+12
            slope = pLine['a']
            intercept = pLine['b']
            if slope == 0:
                pass
            a, b = self.calcNormalLine(pt, slope, intercept)
            if a == 0 and b == 0:
                # normal line = vertical line
                tmpx = pt[1]
                tmpy = pLine['end'][1]
            elif a == 0:
                # normal line = horizontal
                tmpx = pLine['end'][0]
                tmpy = pt[1]
            else:
                tmpx = (b - intercept) / (slope - a)
                tmpy = a * tmpx + b

            tmpDist = self.getDistance(pt, [tmpx, tmpy])

            if self.isPointOnProfilefLine(tmpx, tmpy, pLine):
                if minDist > tmpDist:
                    minDist = tmpDist
                    x = tmpx
                    y = tmpy
                    i = index

        # check vertices
        cV = self.getClosestVertex(pLines, pt)

        if x is None and cV['seg'] == -1: return False

        if x is None and cV['seg'] > -1:
            # vertex is the projected point
            print "here"
            i = cV['seg']
            minDist = cV['d']
            x, y = pLines[i]['end']
        elif x is not None and cV['seg'] > -1:
            if cV['d'] < minDist:
                # vertex is closer than normal line
                i = cV['seg']
                x, y = pLines[i]['end']

        if minDist > distLimit: return False

        return [x, y, i]

    def isPointOnProfilefLine(self, x, y, pLine):
        if pLine['start'][0] < pLine['end'][0]:
            lx = pLine['start'][0]
            hx = pLine['end'][0]
        else:
            lx = pLine['end'][0]
            hx = pLine['start'][0]
        if pLine['start'][1] < pLine['end'][1]:
            ly = pLine['start'][1]
            hy = pLine['end'][1]
        else:
            ly = pLine['end'][1]
            hy = pLine['start'][1]
        if lx <= x <= hx and ly <= y <= hy:
            return True
        return False

    def getClosestVertex(self, pLines, pt):
        d = 1E+12
        segment = 0
        # First and last vertices shouldn't be the closest vertex.
        for index, pLine in enumerate(pLines):
            if index == 0:
                tmpD = self.getDistance(pLine['end'], pt)
                # excluding first vertex
                if self.getDistance(pLine['start'], pt) < tmpD: return {'seg': -1}
            else:
                tmpD = self.getDistance(pLine['end'], pt)
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
            # get Horizontal line
            b = y
            a = 0
            pass
        elif slope == 0:
            # profile line is horizontal line
            # get Vertical line
            a = 0
            b = 0
            pass
        else:
            a = -1 / slope
            b = y - (a * x)
        return [a, b]

    def calcSlopeIntercept(self, pt1, pt2):
        # a: slope, b: intercept
        if pt2[1] == pt1[1]: # horizontal
            a = 0
            b = pt2[1]
        elif pt2[0] == pt1[0]: # vertical
            a = 0
            b = 0
        else:
            a = (pt2[1] - pt1[1]) / (pt2[0] - pt1[0])
            b = pt2[1] - a * pt2[0]
        return [a, b]

    def getDistance(self, pt1, pt2):
        # print pt1
        # print pt2
        # print '----------------------'
        return sqrt(pow((pt2[0] - pt1[0]), 2) + pow((pt2[1] - pt1[1]), 2))

    def addTieLine(self, pt1, pt2):
        self.tieLine.append([pt1, pt2])

    def getTieLines(self):
        return self.tieLine

    def initTieLines(self):
        self.tieLine = []
