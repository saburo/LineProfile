# -*- coding: utf-8 -*-
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg

class PlottingTool:

    def __init__(self):
        self.ax = None
        self.ax2 = None
        self.fig = None
        self.plotWidget = None

    def getPlotWidget(self):

        bgColor = u'#EEEEEE'
        self.fig = Figure(
            figsize=(1, 1),
            tight_layout=False,
            linewidth=0.0,
            subplotpars=mpl.figure.SubplotParams(left=0, bottom=0, right=0.5, top=1, wspace=0, hspace=0)
        )

        font = {'family' : 'arial', 'weight' : 'normal', 'size' : 8}
        rect = self.fig.patch
        rect.set_facecolor(bgColor)

        plotsize = 0.08, 0.15, 0.84, 0.80 # left, bottom, width, height
        self.subplot = self.fig.add_axes(plotsize)
        self.subplot.tick_params(axis='both', which='major', labelsize=9)
        self.subplot.set_xbound(0,100)
        self.subplot.set_ybound(0,10)
        self.formatAxes(self.subplot)
        return FigureCanvasQTAgg(self.fig)

    def addPlotWidget(self, plotFrame):
        layout = plotFrame.layout()
        if layout.count() == 0:
            layout.addWidget(self.getPlotWidget())
        self.plotWidget = layout.itemAt(0).widget()

    def formatAxes(self, axe1, axe2=None, axe1_colors=u'k', axe2_colors=u'k'):
        axe1.grid()
        axe1.tick_params(axis="both", which="major", colors=axe1_colors, direction="in", length=10, width=1, bottom=True, top=False, left=True, right=False)
        axe1.minorticks_on()
        axe1.tick_params(axis="both", which="minor", colors=axe1_colors, direction= "in", length=5, width=1, bottom=True, top=False, left=True, right=False)
        if axe2 is not None:
            axe2.tick_params(axis="y", which="major", colors=axe2_colors, direction= "in", length=10, width=1, bottom=False, top=False, left=False, right=True)
            axe2.minorticks_on()
            axe2.tick_params(axis="y", which="minor", colors=axe2_colors, direction= "in", length=5, width=1, bottom=False, top=False, left=False, right=True)

    def getMarkerSize(self, defaultSize, dataLength):
        maxSize = 50
        if dataLength:
            return  int(maxSize/dataLength) if int(maxSize/dataLength) < defaultSize else defaultSize
        else:
            return defaultSize

    def resetPlot(self):
        if self.ax is not None: self.ax.cla()
        if self.ax2 is not None: self.ax2.cla()
        self.formatAxes(self.ax, self.ax2)
        self.plotWidget.draw()

    def drawPlot(self, pLines, *data, **opt):
        ## default values
        label1 = u'Primary Y'
        color1 = u'red'
        marker1 = u'o'
        markerSize1 = 10
        label2 = u'Secondary Y'
        color2 = u'blue'
        marker2 = u's'
        markerSize2 = 10
        fontSizeY = 9

        labelX = u'Distance [µm]'
        fontSizeX = 9
        ###########

        if 'label1' in opt: label1 = opt['label1']
        if 'color1' in opt: color1 = opt['color1']
        if 'marker1' in opt: marker1 = opt['marker1']
        if 'markerSize1' in opt:
            markerSize1 = opt['markerSize1']
        else:
            markerSize1 = self.getMarkerSize(markerSize1, len(data[0][0]))
        if 'label2' in opt: label2 = opt['label2']
        if 'color2' in opt: color2 = opt['color2']
        if 'marker2' in opt: marker2 = opt['marker2']
        if 'markerSize2' in opt:
            markerSize2 = opt['markerSize2']
        else:
            if data[1]:
                markerSize2 = self.getMarkerSize(markerSize2, len(data[1][0]))
        if 'fontSizeY' in opt: fontSizeY = opt['fontSizeY']
        if 'labelX' in opt: labelX = opt['labelX']
        if 'fontSizeX' in opt: fontSizeX = opt['fontSizeX']

        self.ax = self.plotWidget.figure.get_axes()[0]
        self.ax.cla()
        self.ax.plot(data[0][0], data[0][1], color=color1, marker=marker1, markersize=markerSize1)
        self.ax.set_ylabel(label1, fontsize=fontSizeY)
        self.ax.yaxis.label.set_color(color1)
        self.ax.tick_params(axis='y', colors=color1)
        self.ax.tick_params(axis='y', which='minor', colors=color1)

        if data[1] is not None:
            if self.ax2 is None:
                self.ax2 = self.ax.twinx()
            self.ax2.cla()
            self.ax2.plot(data[1][0], data[1][1], color=color2, marker=marker2, markersize=markerSize2)
            self.ax2.set_ylabel(label2, fontsize=fontSizeY)
            self.ax2.yaxis.label.set_color(color2)
            self.ax2.tick_params(axis='y', colors=color2, labelsize=fontSizeY)
            self.ax2.tick_params(axis='y', which='minor', colors=color2)
        else:
            if self.ax2 is not None:
                self.ax2.cla()
                self.ax2 = None

        # segment divider (vertical lines)
        d = 0

        for i in range(0, len(pLines) - 1):
            d += pLines[i]['d']
            self.ax.axvline(x=d, c=u'red', ls=u'--', lw=3, alpha=0.3)
        self.ax.set_xbound(0, reduce(lambda x,y: x + y['d'], pLines, 0.00))
        self.ax.set_xlabel(labelX, fontsize=fontSizeX)

        # set x-axis start with 0, end with endpoint of profile line
        self.formatAxes(self.ax, self.ax2, color1, color2)
        self.ax.redraw_in_frame()
        self.plotWidget.draw()

    def savePlot(self, fileName):
        self.plotWidget.figure.savefig(str(fileName))
