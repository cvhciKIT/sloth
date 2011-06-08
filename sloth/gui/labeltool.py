#!/usr/bin/python
import sys, os
import functools, importlib
import fnmatch
from optparse import OptionParser
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import PyQt4.uic as uic
from sloth.gui import qrc_icons
from sloth.gui.buttonarea import *
from sloth.annotations.model import *
from sloth.annotations.container import AnnotationContainerFactory, AnnotationContainer
from sloth.gui.annotationscene import *
from sloth.gui.frameviewer import *
from sloth.gui.controlbuttons import *
from sloth.conf import config
from sloth.core.utils import import_callable
from sloth import APP_NAME, ORGANIZATION_NAME, ORGANIZATION_DOMAIN, VERSION

import okapy.videoio as okv

GUIDIR=os.path.join(os.path.dirname(__file__))

class MainWindow(QMainWindow):
    def __init__(self, argv, parent=None):
        super(MainWindow, self).__init__(parent)

        # parse command line options
        options, args = self.parseCommandLineOptions(argv)
        if options.config != "":
            # load config
            config.update(options.config)

        self.container_factory_ = AnnotationContainerFactory(config.CONTAINERS)
        self.container_ = AnnotationContainer()
        self.current_index_ = None

        self.setupGui()

        self.loadApplicationSettings()
        self.updateStatus()
        self.updateViews()

        if len(args) > 0:
            self.loadInitialFile(args[0])
        else:
            self.loadInitialFile()

        self.loadPlugins(config.PLUGINS)
        self.initShortcuts()

    def parseCommandLineOptions(self, argv):
        usage   = "Usage: %prog [-c config.py] [annotation_file]"
        version = "%prog " + VERSION

        parser = OptionParser(usage=usage, version=version)
        parser.add_option("-c", "--config",  action="store", type="string", default="",   help="Configuration file.")

        return parser.parse_args(argv)

    def loadPlugins(self, plugins):
        # TODO clean up, make configurable
        self.plugins_ = []
        for plugin in plugins:
            if type(plugin) == str:
                plugin = import_callable(plugin)
            p = plugin(self)
            self.plugins_.append(p)
            action = p.action()
            self.ui.menuPlugins.addAction(action)

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
        self.controls.back_button.clicked.connect(self.gotoPrevious)
        self.controls.forward_button.clicked.connect(self.gotoNext)

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
        self.ui.actionNext.      triggered.connect(self.gotoNext)
        self.ui.actionPrevious.  triggered.connect(self.gotoPrevious)
        self.ui.actionZoom_In.   triggered.connect(functools.partial(self.view.setScaleRelative, 1.2))
        self.ui.actionZoom_Out.  triggered.connect(functools.partial(self.view.setScaleRelative, 1/1.2))

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
        if self.container_.filename() is not None:
            filename = QVariant(QString(self.container_.filename()))
        else:
            filename = QVariant()
        settings.setValue("LastFile", filename)


    ###
    ### Annoation file handling
    ###___________________________________________________________________________________________
    def loadAnnotations(self, fname):
        fname = str(fname) # convert from QString
        try:
            self.container_ = self.container_factory_.create(fname)
            self.container_.load(fname)
            msg = "Successfully loaded %s (%d files, %d annotations)" % \
                    (fname, self.container_.numFiles(), self.container_.numAnnotations())
        except Exception, e:
            msg = "Error: Loading failed (%s)" % str(e)
        self.updateStatus(msg)
        self.updateViews()

    def saveAnnotations(self, fname):
        success = False
        try:
            # create new container if the filename is different
            if fname != self.container_.filename():
                # TODO: skip if it is the same class
                newcontainer = self.container_factory_.create(fname)
                newcontainer.setAnnotations(self.container_.annotations())
                self.container_ = newcontainer

            self.container_.save(fname)
            #self.model_.writeback() # write back changes that are cached in the model itself, e.g. mask updates
            msg = "Successfully saved %s (%d files, %d annotations)" % \
                    (fname, self.container_.numFiles(), self.container_.numAnnotations())
            success = True
            self.model_.setDirty(False)
        except Exception as e:
            msg = "Error: Saving failed (%s)" % str(e)

        self.updateStatus(msg)
        return success

    def loadInitialFile(self, fname=None):
        if fname is not None:
            if QFile.exists(fname):
                self.loadAnnotations(fname)
        else:
            settings = QSettings()
            fname = settings.value("LastFile").toString()
            if (not fname.isEmpty()) and QFile.exists(fname):
                self.loadAnnotations(fname)

    def okToContinue(self):
        if self.model_.dirty():
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
        if not self.okToContinue():
            return
        self.container_.clear()
        self.updateStatus()
        self.updateViews()

    def fileOpen(self):
        if not self.okToContinue():
            return
        path = '.'
        if (self.container_.filename() is not None) and \
                (len(self.container_.filename()) > 0):
            path = QFileInfo(self.container_.filename()).path()

        # TODO: compile a list from all the patterns in self.container_factory_
        format_str = ' '.join(['*'])
        fname = QFileDialog.getOpenFileName(self, 
                "%s - Load Annotations" % APP_NAME, path,
                "%s annotation files (%s)" % (APP_NAME, format_str))
        if not fname.isEmpty():
            self.loadAnnotations(fname)

    def fileSave(self):
        if self.container_.filename() is None:
            return self.fileSaveAs()
        return self.saveAnnotations(self.container_.filename())

    def fileSaveAs(self):
        fname = '.'  # self.annotations.filename() or '.'
        format_str = ' '.join(['*.txt'])
        fname = QFileDialog.getSaveFileName(self,
                "%s - Save Annotations" % APP_NAME, fname,
                "%s annotation files (%s)" % (APP_NAME, format_str))

        if not fname.isEmpty():
            return self.saveAnnotations(str(fname))
        return False

    def gotoNext(self):
        # TODO move this to the scene
        if self.model_ is not None and self.current_index_ is not None:
            next_index = self.model_.getNextIndex(self.current_index_)
            self.setCurrentIndex(next_index)

    def gotoPrevious(self):
        # TODO move this to the scene
        if self.model_ is not None and self.current_index_ is not None:
            prev_index = self.model_.getPreviousIndex(self.current_index_)
            self.setCurrentIndex(prev_index)

    def updateStatus(self, message=''):
        self.statusBar().showMessage(message, 5000)
        if self.container_.filename() is not None:
            self.setWindowTitle("%s - %s[*]" % \
                (APP_NAME, QFileInfo(self.container_.filename()).fileName()))
        else:
            self.setWindowTitle("%s - Unnamed[*]" % APP_NAME)
        self.updateModified()

    def updateViews(self):
        self.model_ = AnnotationModel(self.container_.annotations())
        if self.container_.filename() is not None:
            self.model_.setBasedir(os.path.dirname(self.container_.filename()))
        else:
            self.model_.setBasedir("")
        self.model_.dirtyChanged.connect(self.updateModified)

        self.treeview.setModel(self.model_)
        self.scene.setModel(self.model_)
        self.treeview.selectionModel().currentChanged.connect(self.setCurrentIndex)

    def updateModified(self):
        """update all GUI elements which depend on the state of the model,
        e.g. whether it has been modified since the last save"""
        #self.ui.action_Add_Image.setEnabled(self.model_ is not None)
        # TODO also disable/enable other items
        #self.ui.actionSave.setEnabled(self.annotations.dirty())
        #self.setWindowModified(self.annotations.dirty())
        pass

    def currentIndex(self):
        return self.current_index_

    def setCurrentIndex(self, index):
        assert index.isValid()
        newindex = index.model().imageIndex(index)
        if newindex.isValid() and newindex != self.current_index_:
            self.current_index_ = newindex
            self.scene.setRoot(self.current_index_)
            item = index.model().itemFromIndex(self.current_index_)
            if isinstance(item, FrameModelItem):
                self.controls.setFrameNumAndTimestamp(item.framenum(), item.timestamp())
            elif isinstance(item, ImageFileModelItem):
                self.controls.setFilename(os.path.basename(item.filename()))
            if index != self.treeview.currentIndex():
                self.treeview.setCurrentIndex(self.current_index_)

    def addImageFile(self, fname):
        fileitem = {
                'filename': fname,
                'type': 'image',
                'annotations': [ ],
            }
        self.model_.root_.addFile(fileitem)

    def addVideoFile(self, fname):
        fileitem = {
                'filename': fname,
                'type': 'video',
                'frames': [ ],
            }

        # FIXME: OKAPI should provide a method to get all timestamps at once
        # FIXME: Some dialog should be displayed, telling the user that the
        # video is being loaded/indexed and that this might take a while
        video = okv.FFMPEGIndexedVideoSource(fname)
        i = 0
        while video.getNextFrame():
            ts = video.getTimestamp()
            frame = { 'annotations': [],
                      'num': i,
                      'timestamp': ts,
                    }
            fileitem['frames'].append(frame)
            i += 1

        self.model_.root_.addFile(fileitem)

    def addMediaFile(self):
        path = '.'
        if (self.container_.filename() is not None) and \
                (len(self.container_.filename()) > 0):
            path = QFileInfo(self.container_.filename()).path()

        image_types = [ '*.jpg', '*.bmp', '*.png', '*.pgm', '*.ppm', '*.ppm', '*.tif', '*.gif' ]
        video_types = [ '*.mp4', '*.mpg', '*.mpeg', '*.avi', '*.mov', '*.vob' ]
        format_str = ' '.join(image_types + video_types)
        fname = QFileDialog.getOpenFileName(self, "%s - Add Media File" % APP_NAME, path, "Media files (%s)" % (format_str, ))

        if fname.isEmpty():
            return

        fname = str(fname)

        for pattern in image_types:
            if fnmatch.fnmatch(fname, pattern):
                return self.addImageFile(fname)

        return self.addVideoFile(fname)


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


