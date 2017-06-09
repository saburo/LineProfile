# -*- coding: utf-8 -*-
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.colors import ColorConverter
from mpl_toolkits.axes_grid1.parasite_axes import SubplotHost
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import mpl_toolkits.axisartist as AA
from PyQt4.QtCore import Qt
import numpy as np

class PlottingTool:

    def __init__(self, model, tracer):
        self.fig = None
        self.host = None
        self.par = []
        self.plotWidget = None
        self.model = model
        self.mcv = None
        self.cid = None
        self.tracer = tracer

    def getPlotWidget(self):
        bgColor = u'#F9F9F9'
        bgColor = u'#E4E4E4'
        spp = mpl.figure.SubplotParams(left=0, bottom=0,
                                       right=1, top=1, 
                                       wspace=0, hspace=0)
        self.fig = Figure(figsize=(1, 1),
                          tight_layout=True,
                          linewidth=0.0, subplotpars=spp)
        rect = self.fig.patch.set_facecolor(bgColor)
        self.mcv = FigureCanvas(self.fig)
        return self.mcv

    def addPlotWidget(self, plotFrame):
        layout = plotFrame.layout()
        if layout.count() == 0:
            layout.addWidget(self.getPlotWidget())
        self.plotWidget = layout.itemAt(0).widget()

    # def formatAxes(self, axe1, axe2=None, axe1_colors=u'k', axe2_colors=u'k'):
    #     # add grrid to the plot
    #     axe1.grid()
    #     # major ticks for left axis with color
    #     axe1.tick_params(axis="y", which="major", colors=axe1_colors,
    #                      direction="in", length=10, width=1, bottom=True,
    #                      top=False, left=True, right=False)
    #     # minor ticks for left axis with color
    #     axe1.minorticks_on()
    #     axe1.tick_params(axis="y", which="minor", colors=axe1_colors,
    #                      direction="in", length=5, width=1, bottom=True,
    #                      top=False, left=True, right=False)

        
    #     # for X axis
    #     # major tick
    #     axe1.tick_params(axis="x", which="major", colors=u'k',
    #                      direction="in", length=10, width=1, bottom=True,
    #                      top=False, left=True, right=False)
    #     # minor tick
    #     axe1.tick_params(axis="x", which="minor", colors=u'k',
    #                      direction="in", length=5, width=1, bottom=True,
    #                      top=False, left=True, right=False)

    #     if axe2 is not None:
    #         axe2.tick_params(axis="y", which="major", colors=axe2_colors,
    #                          direction="in", length=10, width=1, bottom=False,
    #                          top=False, left=False, right=True)
    #         axe2.minorticks_on()
    #         axe2.tick_params(axis="y", which="minor", colors=axe2_colors,
    #                          direction="in", length=5, width=1, bottom=False,
    #                          top=False, left=False, right=True)

    def getMarkerSize(self, defaultSize, dataLength):
        maxSize = 30
        if dataLength:
            if int(maxSize / dataLength) < defaultSize:
                return int(maxSize / dataLength)
            else:
                return defaultSize
        else:
            return defaultSize

    # def resetPlot(self):
    #     if self.ax is not None:
    #         self.ax.cla()
    #     if self.ax2 is not None:
    #         self.ax2.cla()
    #     self.formatAxes(self.ax, self.ax2)
    #     self.plotWidget.draw()

    def calculateMovingAverage(self, data, N=10):
        offset = 0 if N % 2.0 else 1
        n2 = int(N / 2.0)
        maY = np.convolve(data[1], np.ones((N,))/N, mode='valid')
        maX = data[0][n2:len(data[0]) - n2 + offset]
        return (maX, maY)
    
    def movingAverage(self, host, data, color, N=10, linestyle='-'):
        maX, maY = self.calculateMovingAverage(data, N)
        movAve, = host.plot(maX, maY, color=color, linestyle=linestyle)

    def drawPlot3(self, pLines, data, **opt):
        # clear current plot
        self.resetPlot()
        self.par = []

        AxisPadding = 0.1

        dataN = 0
        linestyles = ['-', ':', '--', ':']
        linewidth = [1, 1.5, 1.8, 2]
        symbolAlpha = [1, 0.6, 0.3]

        pLineNorm = opt['pLineNormalize']

        normFactor = []
        if pLineNorm:
            deno = reduce(lambda x, y: x + y['d'], pLines[0], 0.00)
            for pIndex in xrange(len(pLines)):
                normFactor.append(deno / reduce(lambda x, y: x + y['d'], pLines[pIndex], 0.00))
        else:
            for pIndex in xrange(len(pLines)):
                normFactor.append(1)

        longestN = 0
        longestIndex = 0
        for d in xrange(len(data)):
            if longestN < len(data[d]):
                longestN = len(data[d])
                longestIndex = d

        for d in data[longestIndex]:
            dataN += 1
            # print map(data, lambda x: len(x['data']))
            if d['layer_type'] and d['configs']['movingAverage']:
                for pIndex in xrange(len(data)):
                    if not len(data[pIndex]):
                        continue
                    dd = data[pIndex][dataN-1]
                    tmp = map(lambda x: x * normFactor[pIndex], dd['data'][0])
                    dd['data'][0] = tmp
                    self.movingAverage(self.host, dd['data'], 
                                       dd['color_org'], 
                                       dd['configs']['movingAverageN'],
                                       linestyles[pIndex])
            # else:
            #     color = d['color_org']

            if dataN == 1: # host data (1st data)
                for pIndex in xrange(len(data)):
                    if not len(data[pIndex]):
                        continue
                    dd = data[pIndex][dataN-1]
                    tmp = map(lambda x: x * normFactor[pIndex], dd['data'][0])
                    dd['data'][0] = tmp
                    if d['layer_type'] and d['configs']['movingAverage']:
                        color = ColorConverter().to_rgba(d['color_org'], alpha=0.1)
                    else:
                        color = ColorConverter().to_rgba(d['color_org'], alpha=symbolAlpha[pIndex])
                    leftA, = self.host.plot(dd['data'][0], dd['data'][1], 
                                            label=dd['label'], color=color,
                                            linestyle=linestyles[pIndex],
                                            linewidth=linewidth[pIndex],
                                            marker=u'o',
                                            markersize=self.getMarkerSize(10, len(dd['data'][0])))
                self.host.set_ylabel(d['label'])
                self.host.set_xlabel(u"Distance [µm]")
                self.host.minorticks_on()
                self.host.axis["bottom"].label.set_fontsize(10)
                self.host.axis["bottom"].major_ticklabels.set_fontsize(8)
                self.host.axis["left"].major_ticklabels.set_fontsize(8)
                self.host.axis["left"].label.set_color(d['color_org'])
                self.cid = self.mcv.mpl_connect('motion_notify_event', lambda event: self.tracer(event, normFactor))
                # other connectable event 'button_release_event'
            else: # after second plot (data)
            # parasite axes
                self.par.append(self.host.twinx())
                j = len(self.par) - 1
                # isolated axes
                if j > 0:
                    offset = 50 * j
                    new_fixed_axis = self.par[j].get_grid_helper().new_fixed_axis
                    self.par[j].axis["right"] = new_fixed_axis(loc="right",
                                                               axes=self.par[j],
                                                               offset=(offset, 0))
                    self.par[j].axis["right"].toggle(all=True)
                for pIndex in xrange(len(data)):
                    if not len(data[pIndex]):
                        continue
                    dd = data[pIndex][dataN-1]
                    tmp = map(lambda x: x * normFactor[pIndex], dd['data'][0])
                    dd['data'][0] = tmp
                    if d['layer_type'] and d['configs']['movingAverage']:
                        color = ColorConverter().to_rgba(d['color_org'], alpha=0.1)
                    else:
                        color = ColorConverter().to_rgba(d['color_org'], alpha=symbolAlpha[pIndex])
                    tmp, = self.par[j].plot(dd['data'][0], dd['data'][1],
                                            label=dd['label'], color=color,
                                            linestyle=linestyles[pIndex],
                                            linewidth=linewidth[pIndex],
                                            marker=u's',
                                            markersize=self.getMarkerSize(10, len(dd['data'][0])))
                self.par[j].set_ylabel(d['label'])
                self.par[j].minorticks_on()
                self.par[j].axis["right"].major_ticklabels.set_fontsize(8)
                self.par[j].axis["right"].label.set_fontsize(10)
                self.par[j].axis["right"].label.set_color(d['color_org'])
                # rotate right-labels 180 deg.
                self.par[j].axis["right"].label.set_axis_direction('left')
                myRange = self.par[j].axis()
                myMargin = (myRange[3] - myRange[2]) * AxisPadding
                self.par[j].set_ylim(myRange[2]-myMargin, myRange[3]+myMargin)

        # draw vertical line for 
        plColor = [u'red', u'blue']
        for pIndex in xrange(len(pLines)):
            d = 0
            for i in xrange(len(pLines[pIndex])-1):
                d += pLines[pIndex][i]['d']
                self.host.axvline(x=d * normFactor[pIndex], c=plColor[pIndex], ls=u':', lw=1, alpha=0.3)

        # set x-axis start with 0, end with endpoint of profile line
        dMax = []
        # for pL in pLines:
        for pIndex in xrange(len(pLines)):
            pL = pLines[pIndex]
            dMax.append(reduce(lambda x, y: x + y['d'] * normFactor[pIndex], pL, 0.00))

        self.host.set_xlim(0, max(dMax))
        myRange = self.host.axis()
        myMargin = (myRange[3] - myRange[2]) * AxisPadding
        self.host.set_ylim(myRange[2]-myMargin, myRange[3]+myMargin)

        self.plotWidget.draw()

    def drawPlot4(self, pLines, data, **opt):
        # clear current plot
        self.resetPlot()
        self.par = []

        dataN = 0
        for d in data:
            dataN += 1
            if d['layer_type'] and d['configs']['movingAverage']:
                color = ColorConverter().to_rgba(d['color_org'], alpha=0.1)
                self.movingAverage(self.host, d['data'], 
                                   d['color_org'], d['configs']['movingAverageN'])
            else:
                color = d['color_org']

            if dataN == 1: # host data (1st data)
                leftA, = self.host.plot(d['data'][0], d['data'][1], 
                                        label=d['label'], c=color,
                                        marker=u'o',
                                        linewith=linewidth[pIndex],
                                        markersize=self.getMarkerSize(10, len(d['data'][0])))
                self.host.set_ylabel(d['label'])
                self.host.set_xlabel(u"Distance [µm]")
                self.host.minorticks_on()
                self.host.axis["bottom"].label.set_fontsize(10)
                self.host.axis["bottom"].major_ticklabels.set_fontsize(8)
                self.host.axis["left"].major_ticklabels.set_fontsize(8)
                self.host.axis["left"].label.set_color(d['color_org'])
                self.cid = self.mcv.mpl_connect('motion_notify_event', self.tracer)
                # other connectable event 'button_release_event'
            else: # after second plot (data)
            # parasite axes
                self.par.append(self.host.twinx())
                j = len(self.par) - 1
                # isolated axes
                if j > 0:
                    offset = 50 * j
                    new_fixed_axis = self.par[j].get_grid_helper().new_fixed_axis
                    self.par[j].axis["right"] = new_fixed_axis(loc="right",
                                                               axes=self.par[j],
                                                               offset=(offset, 0))
                    self.par[j].axis["right"].toggle(all=True)
                tmp, = self.par[j].plot(d['data'][0], d['data'][1],
                                        label=d['label'], c=color,
                                        marker=u's',
                                        linewith=linewidth[pIndex],
                                        markersize=self.getMarkerSize(10, len(d['data'][0])))
                self.par[j].set_ylabel(d['label'])
                self.par[j].minorticks_on()
                self.par[j].axis["right"].major_ticklabels.set_fontsize(8)
                self.par[j].axis["right"].label.set_fontsize(10)
                self.par[j].axis["right"].label.set_color(d['color_org'])

        # draw vertical line for 
        d = 0
        for i in range(0, len(pLines) - 1):
            d += pLines[i]['d']
            self.host.axvline(x=d, c=u'red', ls=u'--', lw=1, alpha=0.3)

        # set x-axis start with 0, end with endpoint of profile line
        self.host.set_xlim(0, reduce(lambda x, y: x + y['d'], pLines, 0.00))
        self.plotWidget.draw()

    def resetPlot(self, clearAll=False):
        if self.cid:
            self.mcv.mpl_disconnect(self.cid)
        try:
            self.fig.delaxes(self.host)
            self.host.clear()
            [i.cla() for i in self.par]
            if clearAll:
                self.mcv.draw()
        except:
            pass
        self.host = self.fig.add_axes(AA.SubplotHost(self.fig, 111))
        print self.host

    def savePlot(self, fileName):
        self.plotWidget.figure.savefig(str(fileName))
