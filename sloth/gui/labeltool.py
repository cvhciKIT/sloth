#!/usr/bin/python
import os
import functools
import fnmatch
from PyQt4.QtGui import QMainWindow, QSizePolicy, QWidget, QVBoxLayout, QAction,\
        QKeySequence, QLabel, QItemSelectionModel, QMessageBox, QFileDialog, QFrame, \
        QDockWidget
from PyQt4.QtCore import SIGNAL, QSettings, QSize, QPoint, QVariant, QFileInfo
import PyQt4.uic as uic
from sloth.gui import qrc_icons  # needed for toolbar icons
from sloth.gui.propertyeditor import PropertyEditor
from sloth.gui.annotationscene import AnnotationScene
from sloth.gui.frameviewer import GraphicsView
from sloth.gui.controlbuttons import ControlButtonWidget
from sloth.conf import config
from sloth.core.utils import import_callable
from sloth.annotations.model import AnnotationTreeView, FrameModelItem, ImageFileModelItem
from sloth import APP_NAME, ORGANIZATION_DOMAIN

GUIDIR=os.path.join(os.path.dirname(__file__))

def bind(function, labeltool):
    return lambda: function(labeltool)

class MainWindow(QMainWindow):
    def __init__(self, labeltool, parent=None):
        QMainWindow.__init__(self, parent)

        self.labeltool = labeltool
        self.setupGui()
        self.loadApplicationSettings()
        self.onAnnotationsLoaded()

    # Slots
    def onPluginLoaded(self, action):
        self.ui.menuPlugins.addAction(action)

    def onStatusMessage(self, message=''):
        self.statusBar().showMessage(message, 5000)

    def onModelDirtyChanged(self, dirty):
        postfix = "[+]" if dirty else ""
        if self.labeltool.getCurrentFilename() is not None:
            self.setWindowTitle("%s - %s %s" % \
                (APP_NAME, QFileInfo(self.labeltool.getCurrentFilename()).fileName(), postfix))
        else:
            self.setWindowTitle("%s - Unnamed %s" % (APP_NAME, postfix))

    def onMousePositionChanged(self, x, y):
        self.posinfo.setText("%d, %d" % (x, y))

    def onAnnotationsLoaded(self):
        self.labeltool.model().dirtyChanged.connect(self.onModelDirtyChanged)
        self.onModelDirtyChanged(self.labeltool.model().dirty())
        self.treeview.setModel(self.labeltool.model())
        self.scene.setModel(self.labeltool.model())
        self.selectionmodel = QItemSelectionModel(self.labeltool.model())
        self.treeview.setSelectionModel(self.selectionmodel)
        self.treeview.selectionModel().currentChanged.connect(self.labeltool.setCurrentImage)
        self.property_editor.onModelChanged(self.labeltool.model())

    def onCurrentImageChanged(self):
        new_image = self.labeltool.currentImage()
        self.scene.setCurrentImage(new_image)
        self.treeview.scrollTo(new_image.index())

        img = self.labeltool.getImage(new_image)

        h = img.shape[0]
        w = img.shape[1]
        self.image_resolution.setText("%dx%d" % (w, h))

        # TODO: This info should be obtained from AnnotationModel or LabelTool
        if isinstance(new_image, FrameModelItem):
            self.controls.setFrameNumAndTimestamp(new_image.framenum(), new_image.timestamp())
        elif isinstance(new_image, ImageFileModelItem):
            self.controls.setFilename(os.path.basename(new_image['filename']))

        self.selectionmodel.setCurrentIndex(new_image.index(), QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)

    def onScaleChanged(self, scale):
        self.zoominfo.setText("%.2f%%" % (100 * scale, ))

    def initShortcuts(self, HOTKEYS):
        self.shortcuts = []

        for hotkey in HOTKEYS:
            assert len(hotkey) >= 2
            key = hotkey[0]
            fun = hotkey[1]
            desc = ""
            if len(hotkey) > 2:
                desc = hotkey[2]
            if type(fun) == str:
                fun = import_callable(fun)

            hk = QAction(desc, self)
            hk.setShortcut(QKeySequence(key))
            hk.setEnabled(True)
            hk.triggered.connect(bind(fun, self.labeltool))
            self.ui.menuShortcuts.addAction(hk)
            self.shortcuts.append(hk)

    ###
    ### GUI/Application setup
    ###___________________________________________________________________________________________
    def setupGui(self):
        self.ui = uic.loadUi(os.path.join(GUIDIR, "labeltool.ui"), self)

        # get inserters and items from labels
        # FIXME for handling the new-style config correctly
        inserters = dict([(label['attributes']['class'], label['inserter']) 
                          for label in config.LABELS
                          if 'class' in label.get('attributes', {}) and 'inserter' in label])
        items = dict([(label['attributes']['class'], label['item']) 
                      for label in config.LABELS
                      if 'class' in label.get('attributes', {}) and 'item' in label])

        # Property Editor
        self.property_editor = PropertyEditor(config.LABELS)
        self.ui.dockProperties.setWidget(self.property_editor)

        # Scene
        self.scene = AnnotationScene(self.labeltool, items=items, inserters=inserters)
        self.property_editor.insertionModeStarted.connect(self.scene.onInsertionModeStarted)
        self.property_editor.insertionModeEnded.connect(self.scene.onInsertionModeEnded)

        # SceneView
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

        self.initShortcuts(config.HOTKEYS)

        self.treeview = AnnotationTreeView()
        self.treeview.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.ui.dockAnnotations.setWidget(self.treeview)

        self.scene.selectionChanged.connect(self.scene.onSelectionChanged)
        self.treeview.selectedItemsChanged.connect(self.scene.onSelectionChangedInTreeView)

        self.posinfo = QLabel("-1, -1")
        self.posinfo.setFrameStyle(QFrame.StyledPanel)
        self.statusBar().addPermanentWidget(self.posinfo)
        self.scene.mousePositionChanged.connect(self.onMousePositionChanged)

        self.image_resolution = QLabel("[no image]")
        self.image_resolution.setFrameStyle(QFrame.StyledPanel)
        self.statusBar().addPermanentWidget(self.image_resolution)

        self.zoominfo = QLabel()
        self.zoominfo.setFrameStyle(QFrame.StyledPanel)
        self.statusBar().addPermanentWidget(self.zoominfo)
        self.view.scaleChanged.connect(self.onScaleChanged)
        self.onScaleChanged(self.view.getScale())

        # View menu
        self.ui.menu_Views.addAction(self.ui.dockProperties.toggleViewAction())
        self.ui.menu_Views.addAction(self.ui.dockAnnotations.toggleViewAction())

        # Show the UI.  It is important that this comes *after* the above 
        # adding of custom widgets, especially the central widget.  Otherwise the
        # dock widgets would be far to large.
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

        ## View menu
        self.ui.actionLocked.toggled.connect(self.onViewsLockedChanged)

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
        self.labeltool.currentImageChanged.connect(self.onCurrentImageChanged)

    def loadApplicationSettings(self):
        settings = QSettings()
        size   = settings.value("MainWindow/Size", QSize(800, 600))
        pos    = settings.value("MainWindow/Position", QPoint(10, 10))
        state  = settings.value("MainWindow/State")
        locked = settings.value("MainWindow/ViewsLocked", False)
        if isinstance(size,   QVariant): size  = size.toSize()
        if isinstance(pos,    QVariant): pos   = pos.toPoint()
        if isinstance(state,  QVariant): state = state.toByteArray()
        if isinstance(locked, QVariant): locked = locked.toBool()
        self.resize(size)
        self.move(pos)
        self.restoreState(state)
        self.ui.actionLocked.setChecked(bool(locked))

    def saveApplicationSettings(self):
        settings = QSettings()
        settings.setValue("MainWindow/Size",        self.size())
        settings.setValue("MainWindow/Position",    self.pos())
        settings.setValue("MainWindow/State",       self.saveState())
        settings.setValue("MainWindow/ViewsLocked", self.ui.actionLocked.isChecked())
        if self.labeltool.getCurrentFilename() is not None:
            filename = self.labeltool.getCurrentFilename()
        else:
            filename = None
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
            self.labeltool.loadAnnotations(fname)

    def fileSave(self):
        filename = self.labeltool.getCurrentFilename()
        if filename is None:
            return self.fileSaveAs()
        return self.labeltool.saveAnnotations(filename)

    def fileSaveAs(self):
        fname = '.'  # self.annotations.filename() or '.'
        format_str = ' '.join(self.labeltool.getAnnotationFilePatterns())
        fname = QFileDialog.getSaveFileName(self,
                "%s - Save Annotations" % APP_NAME, fname,
                "%s annotation files (%s)" % (APP_NAME, format_str))

        if not fname.isEmpty():
            return self.labeltool.saveAnnotations(str(fname))
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

    def onViewsLockedChanged(self, checked):
        features = QDockWidget.AllDockWidgetFeatures
        if checked:
            features = QDockWidget.NoDockWidgetFeatures 

        self.ui.dockProperties.setFeatures(features)
        self.ui.dockAnnotations.setFeatures(features)


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


