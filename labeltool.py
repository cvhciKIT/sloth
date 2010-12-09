#!/usr/bin/python
import sys, os
import functools
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import PyQt4.uic as uic
import qrc_icons
from buttonarea import *
from annotationmodel import *
from annotationscene import *
from frameviewer import *
import annotations


APP_NAME            = """labeltool"""
ORGANIZATION_NAME   = """CVHCI Research Group"""
ORGANIZATION_DOMAIN = """cvhci.anthropomatik.kit.edu"""
__version__         = """0.1"""

class MainWindow(QMainWindow):
    def __init__(self, argv, parent=None):
        super(MainWindow, self).__init__(parent)
        self.anno_container = annotations.AnnotationContainer()
        self.current_index_ = None

        self.setupGui()

        self.loadApplicationSettings()
        self.updateStatus()
        self.updateViews()

        if len(argv) > 0:
            self.loadInitialFile(argv[0])
        else:
            self.loadInitialFile()

    ###
    ### GUI/Application setup
    ###___________________________________________________________________________________________
    def setupGui(self):
        self.ui = uic.loadUi("labeltool.ui", self)
        self.ui.show()

        self.view = GraphicsView(self)
        self.setCentralWidget(self.view)

        self.scene = AnnotationScene(self)
        self.view.setScene(self.scene)

        self.buttonarea = ButtonArea()
        self.buttonarea.load("example_config.py")
        self.ui.dockAnnotationButtons.setWidget(self.buttonarea)
        self.connect(self.buttonarea, SIGNAL("stateChanged(state)"), self.scene.setMode)

        self.treeview = AnnotationTreeView()
        self.ui.dockInformation.setWidget(self.treeview)

        ## create action group for tools
        self.toolActions = QActionGroup(self)
        for action in (self.ui.actionSelection,
                       self.ui.actionPoint,
                       self.ui.actionRectangle,
                       self.ui.actionMask):
            self.toolActions.addAction(action)

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
        #self.ui.action_Add_Image.triggered.connect(self.addImage)
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
        if self.anno_container.filename() is not None:
            filename = QVariant(QString(self.anno_container.filename()))
        else:
            filename = QVariant()
        settings.setValue("LastFile", filename)

    ###
    ### Annoation file handling
    ###___________________________________________________________________________________________
    def loadAnnotations(self, fname):
        fname = str(fname) # convert from QString
        try:
            self.anno_container.load(fname)
            msg = "Successfully loaded %s (%d files, %d annotations)" % \
                    (fname, self.anno_container.numFiles(), self.anno_container.numAnnotations())
        except Exception as e:
            msg = "Error: Loading failed (%s)" % str(e)
        self.updateStatus(msg)
        self.updateViews()

    def saveAnnotations(self, fname):
        print "TODO: implement file saving"

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
                self.saveAnnotations()
        return True

    def fileNew(self):
        if not self.okToContinue():
            return
        self.anno_container.clear()
        self.updateStatus()
        self.updateViews()

    def fileOpen(self):
        if not self.okToContinue():
            return
        path = '.'
        if (self.anno_container.filename() is not None) and \
                (len(self.anno_container.filename()) > 0):
            path = QFileInfo(self.anno_container.filename()).path()

        #format_str = ' '.join(['*.'+fmt for fmt in self.anno_container.formats()])
        format_str = ' '.join(['*.txt'])
        fname = QFileDialog.getOpenFileName(self, 
                "%s - Load Annotations" % APP_NAME, path,
                "%s annotation files (%s)" % (APP_NAME, format_str))
        if not fname.isEmpty():
            self.loadAnnotations(fname)

    def fileSave(self):
        print "TODO: implement fileSave"
        return False

        if self.annotations.filename() is None:
            return self.fileSaveAs()
        ok, msg = self.annotations.save()
        self.model_.writeback() # write back changes that are cached in the model itself, e.g. mask updates
        self.updateStatus(msg)
        return ok

    def fileSaveAs(self):
        fname = '.'  # self.annotations.filename() or '.'
        format_str = ' '.join(['*.'+fmt for fmt in self.anno_container.formats()])
        fname = QFileDialog.getSaveFileName(self,
                "%s - Save Annotations" % APP_NAME, fname,
                "%s annotation files (%s)" % (APP_NAME, format_str))

        print "TODO: implement fileSaveAs"
        return False

        if not fname.isEmpty():
            if not fname.contains("."):
                fname += ".yaml"
            ok, msg = self.annotations.save(fname)
            self.model_.writeback() # write back changes that are cached in the model itself, e.g. mask updates
            self.updateStatus(msg)
            return ok
        return False

    def gotoNext(self):
        # TODO move this to the scene
        if self.model_ is not None and self.current_index_ is not None:
            next_index = self.model_.getNextIndex(self.current_index_)
            self.setCurrentFileIndex(next_index)

    def gotoPrevious(self):
        # TODO move this to the scene
        if self.model_ is not None and self.current_index_ is not None:
            next_index = self.model_.getNextIndex(self.current_index_)
            self.setCurrentFileIndex(next_index)

    def updateStatus(self, message=''):
        self.statusBar().showMessage(message, 5000)
        if self.anno_container.filename() is not None:
            self.setWindowTitle("%s - %s[*]" % \
                (APP_NAME, QFileInfo(self.anno_container.filename()).fileName()))
        else:
            self.setWindowTitle("%s - Unnamed[*]" % APP_NAME)
        self.updateModified()

    def updateViews(self):
        self.model_ = AnnotationModel(self.anno_container.asDict())
        if self.anno_container.filename() is not None:
            self.model_.setBasedir(os.path.dirname(self.anno_container.filename()))
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

    def setCurrentIndex(self, index):
        assert index.isValid()
        newindex = index.model().imageIndex(index)
        if newindex.isValid() and newindex != self.current_index_:
            self.current_index_ = newindex
            self.scene.setRoot(self.current_index_)
            if index != self.treeview.currentIndex():
                self.treeview.setCurrentIndex(self.current_index_)

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

def main():
    app = QApplication(sys.argv)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setOrganizationDomain(ORGANIZATION_DOMAIN)
    app.setApplicationName(APP_NAME)

    wnd = MainWindow(sys.argv[1:])
    wnd.show()

    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())

