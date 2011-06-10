#!/usr/bin/python
import sys, os
import fnmatch
from optparse import OptionParser
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from sloth.annotations.model import *
from sloth.annotations.container import AnnotationContainerFactory, AnnotationContainer
from sloth.conf import config
from sloth.core.utils import import_callable
from sloth import VERSION

import okapy.videoio as okv

class LabelTool(QObject):
    # Signals
    statusMessage       = pyqtSignal(QString)
    annotationsLoaded   = pyqtSignal()
    pluginLoaded        = pyqtSignal(QAction)
    currentIndexChanged = pyqtSignal(QModelIndex)

    def __init__(self, argv, parent=None):
        QObject.__init__(self, parent)

        # Parse command line options
        options, args = self.parseCommandLineOptions(argv)

        # Load config
        if options.config != "":
            config.update(options.config)

        # Instatiate container factory
        self.container_factory_ = AnnotationContainerFactory(config.CONTAINERS)
        self.container_         = AnnotationContainer()
        self.current_index_     = None

        # Load annotation file
        if len(args) > 0:
            self.loadInitialFile(args[0])
        else:
            self.loadInitialFile()

        # Load plugins
        self.loadPlugins(config.PLUGINS)

    def parseCommandLineOptions(self, argv):
        usage   = "Usage: %prog [-c config.py] [annotation_file]"
        version = "%prog " + VERSION

        parser = OptionParser(usage=usage, version=version)
        parser.add_option("-c", "--config", action="store", type="string", default="", help="Configuration file.")

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
            self.pluginLoaded.emit(action)

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
            self._model = AnnotationModel(self.container_.annotations())
            if self.container_.filename() is not None:
                self._model.setBasedir(os.path.dirname(self.container_.filename()))
            else:
                self._model.setBasedir("")
        except Exception, e:
            msg = "Error: Loading failed (%s)" % str(e)
        self.statusMessage.emit(msg)
        self.annotationsLoaded.emit()

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
            #self._model.writeback() # write back changes that are cached in the model itself, e.g. mask updates
            msg = "Successfully saved %s (%d files, %d annotations)" % \
                    (fname, self.container_.numFiles(), self.container_.numAnnotations())
            success = True
            self._model.setDirty(False)
        except Exception as e:
            msg = "Error: Saving failed (%s)" % str(e)

        self.statusMessage.emit(msg)
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
            else:
                self.clearAnnotations()

    def clearAnnotations(self):
        self.container_.clear()
        self._model = AnnotationModel(self.container_.annotations())
        self._model.setBasedir("")
        self.statusMessage.emit('')
        self.annotationsLoaded.emit()

    def getCurrentFilename(self):
        return self.container_.filename()

    ###########################################################################
    # Model stuff
    ###########################################################################

    def model(self):
        return self._model

    def gotoNext(self):
        # TODO move this to the scene
        if self._model is not None and self.current_index_ is not None:
            next_index = self._model.getNextIndex(self.current_index_)
            self.setCurrentIndex(next_index)

    def gotoPrevious(self):
        # TODO move this to the scene
        if self._model is not None and self.current_index_ is not None:
            prev_index = self._model.getPreviousIndex(self.current_index_)
            self.setCurrentIndex(prev_index)

    def updateModified(self):
        """update all GUI elements which depend on the state of the model,
        e.g. whether it has been modified since the last save"""
        #self.ui.action_Add_Image.setEnabled(self._model is not None)
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
            self.currentIndexChanged.emit(self.current_index_)

    def getAnnotationFilePatterns(self):
        return self.container_factory_.patterns()

    def addImageFile(self, fname):
        fileitem = {
                'filename': fname,
                'type': 'image',
                'annotations': [ ],
            }
        self._model.root_.addFile(fileitem)

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

        self._model.root_.addFile(fileitem)
