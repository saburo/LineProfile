# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LineProfile
                                 A QGIS plugin
 This plugin makes line profile
                              -------------------
        begin                : 2015-02-16
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Kouki Kitajima
        email                : saburo@geology.wisc.edu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QObject, SIGNAL, QSettings, QTranslator, qVersion, QCoreApplication, QVariant
# from PyQt4.QtCore import *
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QColorDialog

from qgis.core import QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsMapLayerRegistry, QgsProject, QgsPoint, QgsVectorFileWriter


# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
# from line_profile_dialog import LineProfileDialog
import os

# Import the code for the DockWidget and ploting
from tools.plottingTool import PlottingTool
from tools.profileLineTool import ProfileLineTool
from tools.dataProcessingTool import DataProcessingTool
from ui.dockWidget import DockWidget
from ui.lpExportDialog import LPExportDialog
from ui.lpImportDialog import LPImportDialog

class LineProfile:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'LineProfile_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        # self.dlg = LineProfileDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Line Profile')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'LineProfile')
        self.toolbar.setObjectName(u'LineProfile')


        # variables
        self.dockOpened = False
        self.dock = None
        # self.plotWdg = None
        self.canvas = self.iface.mapCanvas()
        self.originalMapTool = self.canvas.mapTool()
        self.action = None
        self.mapTool = None
        self.plotTool = None
        self.dpTool = None


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('LineProfile', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/LineProfile/icon.png'
        self.action = self.add_action(
            icon_path,
            text=self.tr(u'Line profile'),
            callback=self.run,
            whats_this=self.tr(u'Plot Line Profiles'),
            parent=self.iface.mainWindow())

        self.profLineTool = ProfileLineTool(self.canvas, self.action)
        self.plotTool = PlottingTool()
        self.dpTool = DataProcessingTool()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Line Profile'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""

        if self.dockOpened == False:
            self.dock = DockWidget(self.iface.mainWindow(), self.iface)
            self.dock.showDockWidget()
            self.plotTool.addPlotWidget(self.dock.myFrame)
            self.dockOpened = True
        QObject.connect(self.canvas, SIGNAL('layersChanged()'), self.refreshDock)
        self.connectDock()
        self.connectTools()
        self.canvas.setMapTool(self.profLineTool)


##############################################################################
    def deactivatePlugin(self):
        QObject.disconnect(self.canvas, SIGNAL('layersChanged()'), self.refreshDock)
        self.canvas.unsetMapTool(self.profLineTool)
        self.canvas.setMapTool(self.originalMapTool)
        self.disconnectDock()
        self.disconnectTools()

    def closePlugin(self):
        self.deactivatePlugin()
        self.dockOpened = False
        print "exit"

    def connectDock(self):
        QObject.connect(self.dock, SIGNAL( "closed(PyQt_PyObject)" ), self.closePlugin)
        QObject.connect(self.dock.myExportProfileLineBtn, SIGNAL("clicked(bool)"), self.openExportProfileLineDialog)
        QObject.connect(self.dock.Btn_ImportProfileLine, SIGNAL("clicked(bool)"), self.openImportProfileLineDialog)
        QObject.connect(self.dock.Btn_ExportPlot, SIGNAL("clicked(bool)"), self.exportPlot)
        QObject.connect(self.dock.Btn_ChangePlotColor, SIGNAL("clicked(bool)"), self.changePlotColor)
        QObject.connect(self.dock.ChkBox_TieLine, SIGNAL("stateChanged(int)"), self.updatePlot)
        QObject.connect(self.dock.Grp_SecondaryY, SIGNAL('clicked()'), self.updatePlot)
        QObject.connect(self.dock.SpnBox_DistanceLimit, SIGNAL('valueChanged(double)'), self.updatePlot)
        QObject.connect(self.dock, SIGNAL('cmboxupdated'), self.updatePlot)

    def connectTools(self):
        QObject.connect(self.profLineTool, SIGNAL('proflineterminated'), self.updatePlot)
        QObject.connect(self.profLineTool, SIGNAL('doubleClicked'), self.resetPlot)
        QObject.connect(self.profLineTool, SIGNAL('deactivate'), self.deactivatePlugin)

    def disconnectDock(self):
        QObject.disconnect(self.dock.myExportProfileLineBtn, SIGNAL("clicked(bool)"), self.openExportProfileLineDialog)
        QObject.disconnect(self.dock.Btn_ImportProfileLine, SIGNAL("clicked(bool)"), self.openImportProfileLineDialog)
        QObject.disconnect(self.dock.Btn_ExportPlot, SIGNAL("clicked(bool)"), self.exportPlot)
        QObject.disconnect(self.dock.Btn_ChangePlotColor, SIGNAL("clicked(bool)"), self.changePlotColor)
        QObject.disconnect(self.dock.ChkBox_TieLine, SIGNAL("stateChanged(int)"), self.updatePlot)
        QObject.disconnect(self.dock.Grp_SecondaryY, SIGNAL('clicked()'), self.updatePlot)
        QObject.disconnect(self.dock.SpnBox_DistanceLimit, SIGNAL('valueChanged(double)'), self.updatePlot)
        QObject.disconnect(self.dock, SIGNAL('cmboxupdated'), self.updatePlot)

    def disconnectTools(self):
        QObject.disconnect(self.profLineTool, SIGNAL('proflineterminated'), self.updatePlot)
        QObject.disconnect(self.profLineTool, SIGNAL('doubleClicked'), self.changePlotColor)
        QObject.disconnect(self.profLineTool, SIGNAL('proflineterminated'), self.updatePlot)

    def changePlotColor(self):
        qd = QColorDialog()
        qd.open()

    def exportPlot(self):
        fileName = QFileDialog.getSaveFileName(self.iface.mainWindow(),
                                                "Save As",
                                                "~/",
                                                "Images (*.png *.jpg);;Portable Document Format (*.pdf);;Scalable Vector Graphics (*.svg)")
        if fileName:
            self.plotTool.savePlot(fileName)

    def refreshDock(self):
        self.dock.updateLayerFieldComboBox()

    def updatePlot(self):
        self.pLines = self.dpTool.getProfileLines(self.profLineTool.getProfPoints())
        if len(self.pLines) == 0: return False

        # initialize tie lines
        self.dpTool.initTieLines()
        self.profLineTool.resetTieLies()

        layer1 = self.getLayerById(self.dock.currentPLayer)
        # layer1 = self.canvas.layer(self.dock.myLayers.currentIndex())
        field1 = self.dock.myFields.currentText()
        if not field1: return False

        distLimit = self.dock.SpnBox_DistanceLimit.value()

        if layer1.type() == 0: # vector
            data1 = self.dpTool.getVectorProfile(self.pLines, layer1, field1, distLimit)
        else:
            data1 = self.dpTool.getRasterProfile(self.pLines, layer1, field1)

        # secondary-Y axis
        if self.dock.Grp_SecondaryY.isChecked():
            layer2 = self.getLayerById(self.dock.currentSLayer)
            # layer2 = self.canvas.layer(self.dock.mySecondLayers.currentIndex())
            field2 = self.dock.mySecondFields.currentText()
            if layer2.type() == 0: # vector
                data2 = self.dpTool.getVectorProfile(self.pLines, layer2, field2, distLimit)
            else:
                data2 = self.dpTool.getRasterProfile(self.pLines, layer2, field2)
        else:
            layer2 = None
            field2 = None
            data2 = None

        # draw tie lines
        if self.dock.ChkBox_TieLine.isChecked():
            for pt in self.dpTool.getTieLines():
                self.profLineTool.drawTieLine(pt[0], pt[1])

        # draw line profile
        self.plotTool.drawPlot( self.pLines,
                                data1, data2,
                                label1=field1,
                                label2=field2)
    def resetPlot(self):
        # self.plotWdg.figure.clear()
        self.plotTool.resetPlot()

    def openExportProfileLineDialog(self):
        self.expPLDialog = LPExportDialog()
        self.expPLDialog.show()
        if self.expPLDialog.exec_():
            if self.expPLDialog.Grp_SaveShapeFileAs.isChecked():
                shapeFilePath = self.sanitizePath(self.expPLDialog.shapeFileName)
                self.exportProfileLineAsShapeFile(shapeFilePath)
            if self.expPLDialog.Grp_AddField.isChecked():
                self.addDistanceToAttribute()

    def exportProfileLineAsShapeFile(self, shapeFilePath):
        fields = []
        polyline = []
        attr = []
        fileName = os.path.basename(shapeFilePath.split(os.extsep)[0])
        profileLineLayer = QgsVectorLayer('LineString', fileName, 'memory')

        profileLineLayer.startEditing()
        dataProvider = profileLineLayer.dataProvider()
        points = self.profLineTool.getProfPoints()

        # add fields
        for i in range(0, len(points)):
            fields.append(QgsField('Point-{0}'.format(i + 1), QVariant.String))
        fields.append(QgsField('Max Dist.', QVariant.Double))
        dataProvider.addAttributes(fields)

        # get profile line features
        for pt in points:
            polyline.append(QgsPoint(pt[0], pt[1]))
            attr.append('{0}, {1}'.format(pt[0], pt[1]))
            # attr.append(pt[1])
        attr.append(self.dock.SpnBox_DistanceLimit.value())

        # add a feature
        feture = QgsFeature()
        feture.setGeometry(QgsGeometry.fromPolyline(polyline))
        feture.setAttributes(attr)
        dataProvider.addFeatures([feture])

        # update layer's extent when new features have been added
        # because change of extent in provider is not propagated to the layer
        profileLineLayer.commitChanges()
        profileLineLayer.updateExtents()

        # save shape file
        error = QgsVectorFileWriter.writeAsVectorFormat(profileLineLayer,
                                                        shapeFilePath,
                                                        'CP1250',
                                                        None,
                                                        'ESRI Shapefile')
        if error == QgsVectorFileWriter.NoError:
            if self.expPLDialog.ChkBox_AddSavedFileToMap.isChecked():
                # add shape file to map
                self.iface.addVectorLayer(shapeFilePath, fileName, 'ogr')
        else:
            print 'Error in file saving process: ' + str(error)

    def addDistanceToAttribute(self):
        layer1 = self.getLayerById(self.dock.currentPLayer)
        field1 = self.dock.myFields.currentText()

        newFieldName = self.expPLDialog.TBox_FieldName.text()

        distLimit = self.dock.SpnBox_DistanceLimit.value()
        if layer1.type() == 0:
            dataProvider = layer1.dataProvider()
            dataProvider.addAttributes([QgsField(newFieldName, QVariant.Double)])
            layer1.updateFields()
            self.dpTool.getVectorProfile(self.pLines, layer1, field1, distLimit, newFieldName)

        if self.dock.Grp_SecondaryY.isChecked():
            layer2 = self.getLayerById(self.dock.currentSLayer)
            field2 = self.dock.mySecondFields.currentText()
            if layer2.type() == 0:
                dataProvider = layer2.dataProvider()
                dataProvider.addAttributes([QgsField(newFieldName, QVariant.Double)])
                layer2.updateFields()
                self.dpTool.getVectorProfile(self.pLines, layer2, field2, distLimit, newFieldName)

    def openImportProfileLineDialog(self):
        self.impPLDialog = LPImportDialog(self.iface)
        self.impPLDialog.show()
        if self.impPLDialog.exec_():
            if self.impPLDialog.RadBtn_FileSelect.isChecked():
                shapeFilePath = self.sanitizePath(self.impPLDialog.TBox_ShapeFilePath.text())
                shapeFileName = os.path.basename(shapeFilePath.split(os.extsep)[0])
                layer = self.iface.addVectorLayer(shapeFilePath , shapeFileName, 'ogr')
            else:
                layerId = self.impPLDialog.CmbBox_LayerSelect.itemData(self.impPLDialog.CmbBox_LayerSelect.currentIndex())
                layer = self.getLayerById(layerId)
            self.importProfileLine(layer)

    def importProfileLine(self, layer):
        dp = layer.dataProvider()
        for f in dp.getFeatures():
            points = f.geometry().asPolyline()
            try:
                maxD = f.attribute('Max Dist.')
            except:
                maxD = self.dock.SpnBox_DistanceLimit.value()

        self.profLineTool.drawProfileLineFromPoints(points)
        self.dock.SpnBox_DistanceLimit.setValue(maxD)
        self.updatePlot()

    def getLayerById(self, lid):
        for layer in self.canvas.layers():
            if lid == layer.id(): return layer
        return False

    def sanitizePath(self, path):
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)
        return os.path.abspath(path)
