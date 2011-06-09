#!/usr/bin/python
import os
import functools, importlib
import fnmatch
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import PyQt4.uic as uic
from sloth.gui import qrc_icons
from sloth.gui.buttonarea import *
from sloth.gui.annotationscene import *
from sloth.gui.frameviewer import *
from sloth.gui.controlbuttons import *
from sloth.conf import config
from sloth.annotations.model import AnnotationTreeView
from sloth import APP_NAME, ORGANIZATION_DOMAIN, VERSION
import okapy.videoio as okv

GUIDIR=os.path.join(os.path.dirname(__file__))

class MainWindow(QMainWindow):
    def __init__(self, labeltool, parent=None):
        QMainWindow.__init__(self, parent)

        self.labeltool = labeltool

        self.setupGui()

        self.loadApplicationSettings()

        self.onAnnotationsLoaded()

        self.initShortcuts()

    # Slots
    def onPluginLoaded(self, action):
        self.ui.menuPlugins.addAction(action)

    def onStatusMessage(self, message=''):
        self.statusBar().showMessage(message, 5000)

    def onAnnotationsLoaded(self):
        if self.labeltool.getCurrentFilename() is not None:
            self.setWindowTitle("%s - %s[*]" % \
                (APP_NAME, QFileInfo(self.labeltool.getCurrentFilename()).fileName()))
        else:
            self.setWindowTitle("%s - Unnamed[*]" % APP_NAME)
        self.treeview.setModel(self.labeltool.model())
        self.scene.setModel(self.labeltool.model())
        self.treeview.selectionModel().currentChanged.connect(self.labeltool.setCurrentIndex)

    def onCurrentIndexChanged(self, new_index):
        self.scene.setRoot(new_index)

        # TODO: This info should be obtained from AnnotationModel or LabelTool
        item = self.labeltool.model().itemFromIndex(new_index)
        if isinstance(item, FrameModelItem):
            self.controls.setFrameNumAndTimestamp(item.framenum(), item.timestamp())
        elif isinstance(item, ImageFileModelItem):
            self.controls.setFilename(os.path.basename(item.filename()))
        if new_index != self.treeview.currentIndex():
            self.treeview.setCurrentIndex(new_index)

    def initShortcuts(self):
        # TODO clean up, make configurable
        self.shortcuts = []

        selectNextItem = QAction("Select next item", self)
        selectNextItem.setShortcut(QKeySequence("Tab"))
        selectNextItem.setEnabled(True)
        selectNextItem.triggered.connect(self.scene.selectNextItem)
        self.ui.menuPlugins.addAction(selectNextItem)
        self.shortcuts.append(selectNextItem)

        selectPreviousItem = QAction("Select previous item", self)
        selectPreviousItem.setShortcut(QKeySequence("Shift+Tab"))
        selectPreviousItem.setEnabled(True)
        selectPreviousItem.triggered.connect(lambda: self.scene.selectNextItem(True))
        self.ui.menuPlugins.addAction(selectPreviousItem)
        self.shortcuts.append(selectPreviousItem)

        exitInsertMode = QAction("Exit insert mode", self)
        exitInsertMode.setShortcut(QKeySequence("ESC"))
        exitInsertMode.setEnabled(True)
        exitInsertMode.triggered.connect(self.buttonarea.exitInsertMode)
        self.ui.menuPlugins.addAction(exitInsertMode)
        self.shortcuts.append(exitInsertMode)

    ###
    ### GUI/Application setup
    ###___________________________________________________________________________________________
    def setupGui(self):
        self.ui = uic.loadUi(os.path.join(GUIDIR, "labeltool.ui"), self)

        self.scene = AnnotationScene(items=config.ITEMS, inserters=config.INSERTERS)
        self.view = GraphicsView(self)
        self.view.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.view.setScene(self.scene)
        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout()
        self.controls = ControlButtonWidget()
        self.controls.back_button.clicked.connect(self.labeltool.gotoPrevious)
        self.controls.forward_button.clicked.connect(self.labeltool.gotoNext)

        self.central_layout.addWidget(self.controls)
        self.central_layout.addWidget(self.view)
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        self.buttonarea = ButtonArea(config.LABELS, config.HOTKEYS)
        self.ui.dockAnnotationButtons.setWidget(self.buttonarea)
        self.buttonarea.stateChanged.connect(self.scene.setMode)

        self.treeview = AnnotationTreeView()
        self.treeview.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.ui.dockInformation.setWidget(self.treeview)

        self.ui.show()

        ## connect action signals
        self.connectActions()

    def connectActions(self):
        ## File menu
        self.connect(self.ui.actionNew,     SIGNAL("triggered()"), self.fileNew)
        self.connect(self.ui.actionOpen,    SIGNAL("triggered()"), self.fileOpen)
        self.connect(self.ui.actionSave,    SIGNAL("triggered()"), self.fileSave)
        self.connect(self.ui.actionSave_As, SIGNAL("triggered()"), self.fileSaveAs)
        self.connect(self.ui.actionExit,    SIGNAL("triggered()"), self.close)

        ## Help menu
        self.ui.action_About.triggered.connect(self.about)

        ## Navigation
        self.ui.action_Add_Image.triggered.connect(self.addMediaFile)
        self.ui.actionNext.      triggered.connect(self.labeltool.gotoNext)
        self.ui.actionPrevious.  triggered.connect(self.labeltool.gotoPrevious)
        self.ui.actionZoom_In.   triggered.connect(functools.partial(self.view.setScaleRelative, 1.2))
        self.ui.actionZoom_Out.  triggered.connect(functools.partial(self.view.setScaleRelative, 1/1.2))

        ## Connections to LabelTool
        self.labeltool.pluginLoaded.       connect(self.onPluginLoaded)
        self.labeltool.statusMessage.      connect(self.onStatusMessage)
        self.labeltool.annotationsLoaded.  connect(self.onAnnotationsLoaded)
        self.labeltool.currentIndexChanged.connect(self.onCurrentIndexChanged)

    def loadApplicationSettings(self):
        settings = QSettings()
        self.resize(settings.value("MainWindow/Size", QVariant(QSize(800, 600))).toSize())
        self.move(settings.value("MainWindow/Position", QVariant(QPoint(10, 10))).toPoint())
        self.restoreState(settings.value("MainWindow/State").toByteArray())

    def saveApplicationSettings(self):
        settings = QSettings()
        settings.setValue("MainWindow/Size",     QVariant(self.size()))
        settings.setValue("MainWindow/Position", QVariant(self.pos()))
        settings.setValue("MainWindow/State",    QVariant(self.saveState()))
        if self.labeltool.getCurrentFilename() is not None:
            filename = QVariant(QString(self.labeltool.getCurrentFilename()))
        else:
            filename = QVariant()
        settings.setValue("LastFile", filename)

    def okToContinue(self):
        if self.labeltool.model().dirty():
            reply = QMessageBox.question(self,
                    "%s - Unsaved Changes" % (APP_NAME),
                    "Save unsaved changes?",
                    QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                return self.fileSave()
        return True

    def fileNew(self):
        if self.okToContinue():
            self.labeltool.clearAnnotations()

    def fileOpen(self):
        if not self.okToContinue():
            return
        path = '.'
        filename = self.labeltool.getCurrentFilename()
        if (filename is not None) and (len(filename) > 0):
            path = QFileInfo(filename).path()

        format_str = ' '.join(self.labeltool.getAnnotationFilePatterns())
        fname = QFileDialog.getOpenFileName(self, 
                "%s - Load Annotations" % APP_NAME, path,
                "%s annotation files (%s)" % (APP_NAME, format_str))
        if not fname.isEmpty():
            self.loadAnnotations(fname)

    def fileSave(self):
        filename = self.labeltool.getCurrentFilename()
        if filename is None:
            return self.fileSaveAs()
        return self.saveAnnotations(filename)

    def fileSaveAs(self):
        fname = '.'  # self.annotations.filename() or '.'
        format_str = ' '.join(self.labeltool.getAnnotationFilePatterns())
        fname = QFileDialog.getSaveFileName(self,
                "%s - Save Annotations" % APP_NAME, fname,
                "%s annotation files (%s)" % (APP_NAME, format_str))

        if not fname.isEmpty():
            return self.saveAnnotations(str(fname))
        return False

    def addMediaFile(self):
        path = '.'
        filename = self.labeltool.getCurrentFilename()
        if (filename is not None) and (len(filename) > 0):
            path = QFileInfo(filename).path()

        image_types = [ '*.jpg', '*.bmp', '*.png', '*.pgm', '*.ppm', '*.ppm', '*.tif', '*.gif' ]
        video_types = [ '*.mp4', '*.mpg', '*.mpeg', '*.avi', '*.mov', '*.vob' ]
        format_str = ' '.join(image_types + video_types)
        fname = QFileDialog.getOpenFileName(self, "%s - Add Media File" % APP_NAME, path, "Media files (%s)" % (format_str, ))

        if fname.isEmpty():
            return

        fname = str(fname)

        for pattern in image_types:
            if fnmatch.fnmatch(fname, pattern):
                return self.labeltool.addImageFile(fname)

        return self.labeltool.addVideoFile(fname)


    ###
    ### global event handling
    ###______________________________________________________________________________
    def closeEvent(self, event):
        if self.okToContinue():
            self.saveApplicationSettings()
        else:
            event.ignore()

    def about(self):
        QMessageBox.about(self, "About %s" % APP_NAME,
             """<b>%s</b> version %s
             <p>This labeling application for computer vision research
             was developed at the CVHCI research group at KIT.
             <p>For more details, visit our homepage: <a href="%s">%s</a>"""
              % (APP_NAME, __version__, ORGANIZATION_DOMAIN, ORGANIZATION_DOMAIN))


