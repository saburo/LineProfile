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
        spp = mpl.figure.SubplotParams(left=0, bottom=0, right=1, top=1, 
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
        maxSize = 40
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
    
    def movingAverage(self, host, data, color, N=10):
        offset = 0 if N % 2.0 else 1
        n2 = int(N / 2.0)
        maY = np.convolve(data[1], np.ones((N,))/N, mode='valid')
        maX = data[0][n2:len(data[0]) - n2 + offset]
        movAve, = host.plot(maX, maY, c=color)

    def drawPlot3(self, pLines, data, **opt):
        # clear current plot
        self.resetPlot()
        
        self.par = []
        dList = [r for r in range(self.model.rowCount()) 
                    if self.model.getCheckState(r) == Qt.Checked]
        # host axis
        r = dList.pop(0)
        hostData = data.pop(0)
        label = unicode(self.model.getDataName(r))
        color_org = unicode(self.model.getColorName(r))
        configs = self.model.getConfigs(r)
        if self.model.getLayerType(r) and configs['movingAverage']:
            color = ColorConverter().to_rgba(color_org, alpha=0.1)
            self.movingAverage(self.host, hostData, 
                               color_org, configs['movingAverageN'])
        else:
            color = color_org
        leftA, = self.host.plot(hostData[0], hostData[1], 
                                label=label, c=color,
                                marker=u'o',
                                markersize=self.getMarkerSize(10, len(hostData[0])))
        self.host.set_ylabel(label)
        self.host.set_xlabel(u"Distance [µm]")
        self.host.minorticks_on()
        self.host.axis["bottom"].label.set_fontsize(10)
        self.host.axis["bottom"].major_ticklabels.set_fontsize(8)
        self.host.axis["left"].major_ticklabels.set_fontsize(8)
        self.host.axis["left"].label.set_color(color_org)
        self.cid = self.mcv.mpl_connect('motion_notify_event', self.tracer)
        # other connectable event 'button_release_event'

        # parasite axes
        for i in data:
            r = dList.pop(0)
            self.par.append(self.host.twinx())
            j = len(self.par) - 1
            configs = self.model.getConfigs(r)
            label = unicode(self.model.getDataName(r))
            color_org = unicode(self.model.getColorName(r))
            if self.model.getLayerType(r) and configs['movingAverage']:
                color = ColorConverter().to_rgba(color_org, alpha=0.1)
            else:
                color = color_org
            # isolated axes
            if j > 0:
                offset = 50 * j
                new_fixed_axis = self.par[j].get_grid_helper().new_fixed_axis
                self.par[j].axis["right"] = new_fixed_axis(loc="right",
                                                           axes=self.par[j],
                                                           offset=(offset, 0))
                self.par[j].axis["right"].toggle(all=True)
            tmp, = self.par[j].plot(i[0], i[1],
                                    label=label, c=color,
                                    marker=u's',
                                    markersize=self.getMarkerSize(10, len(i[0])))
            if self.model.getLayerType(r) and configs['movingAverage']:
                self.movingAverage(self.par[j], i, color_org,
                                   configs['movingAverageN'])
            self.par[j].set_ylabel(label)
            self.par[j].minorticks_on()
            self.par[j].axis["right"].major_ticklabels.set_fontsize(8)
            self.par[j].axis["right"].label.set_fontsize(10)
            self.par[j].axis["right"].label.set_color(color_org)

        # draw vertical line for 
        d = 0
        for i in range(0, len(pLines) - 1):
            d += pLines[i]['d']
            self.host.axvline(x=d, c=u'red', ls=u'--', lw=1, alpha=0.3)

        # set x-axis start with 0, end with endpoint of profile line
        self.host.set_xlim(0, reduce(lambda x, y: x + y['d'], pLines, 0.00))
        self.plotWidget.draw()

    def resetPlot(self):
        if self.cid:
            self.mcv.mpl_disconnect(self.cid)
        try:
            self.fig.delaxes(self.host)
            [i.cla() for i in self.par]
        except:
            pass
        self.host = self.fig.add_axes(AA.SubplotHost(self.fig, 111))

    def savePlot(self, fileName):
        self.plotWidget.figure.savefig(str(fileName))
