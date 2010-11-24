#!/usr/bin/python
import sys, os
import functools
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import PyQt4.uic as uic
import qrc_icons
from buttonarea import *

APP_NAME            = """labeltool"""
ORGANIZATION_NAME   = """CVHCI Research Group"""
ORGANIZATION_DOMAIN = """cvhci.anthropomatik.kit.edu"""
__version__         = """0.1"""

class MainWindow(QMainWindow):
    def __init__(self, argv, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = uic.loadUi("labeltool.ui", self)
        self.ui.show()
        self.view = QGraphicsView(self)
        self.setCentralWidget(self.view)

        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)

        self.buttonarea = ButtonArea()
        self.buttonarea.load("example_config.py")
        self.ui.dockAnnotationTree.setWidget(self.buttonarea)

        ## create action group for tools
        self.toolActions = QActionGroup(self)
        for action in (self.ui.actionSelection,
                       self.ui.actionPoint,
                       self.ui.actionRectangle,
                       self.ui.actionMask):
            self.toolActions.addAction(action)

        ## connect action signals
        self.connectActions()

        self.loadApplicationSettings()
        #self.updateStatus()
        #self.updateViews()

        if len(argv) > 0:
            self.loadInitialFile(argv[0])
        else:
            self.loadInitialFile()

    def loadApplicationSettings(self):
        settings = QSettings()
        self.resize(settings.value("MainWindow/Size", QVariant(QSize(800, 600))).toSize())
        self.move(settings.value("MainWindow/Position", QVariant(QPoint(10, 10))).toPoint())
        self.restoreState(settings.value("MainWindow/State").toByteArray())

    def saveApplicationSettings(self):
        settings = QSettings()
        settings.setValue("MainWindow/Size", QVariant(self.size()))
        settings.setValue("MainWindow/Position", QVariant(self.pos()))
        settings.setValue("MainWindow/State", QVariant(self.saveState()))
        #if self.annotations.filename() is not None:
            #filename = QVariant(QString(self.annotations.filename()))
        #else:
            #filename = QVariant()
        #settings.setValue("LastFile", filename)

    def connectActions(self):
        ## File menu
        self.connect(self.ui.actionNew,     SIGNAL("triggered()"), self.fileNew)
        self.connect(self.ui.actionOpen,    SIGNAL("triggered()"), self.fileOpen)
        self.connect(self.ui.actionSave,    SIGNAL("triggered()"), self.fileSave)
        self.connect(self.ui.actionSave_As, SIGNAL("triggered()"), self.fileSaveAs)
        self.connect(self.ui.actionExit,    SIGNAL("triggered()"), self.close)

        ## Help menu
        self.connect(self.ui.action_About,  SIGNAL("triggered()"), self.about)

        #self.connect(self.ui.action_Add_Image, SIGNAL("triggered()"), self.addImage)
        #self.connect(self.ui.actionNext, SIGNAL("triggered()"), self.gotoNext)
        #self.connect(self.ui.actionPrevious, SIGNAL("triggered()"), self.gotoPrevious)
        #self.connect(self.ui.actionZoom_In, SIGNAL("triggered()"), functools.partial(self.view.scale, 1.2, 1.2))
        #self.connect(self.ui.actionZoom_Out, SIGNAL("triggered()"), functools.partial(self.view.scale, 1/1.2, 1/1.2))

    def loadInitialFile(self, fname=None):
        if fname is not None:
            if QFile.exists(fname):
                print "TODO: implement file loading"
                #ok, msg = self.annotations.load(fname)
                #self.updateStatus(msg)
                #self.updateViews()
        else:
            settings = QSettings()
            fname = settings.value("LastFile").toString()
            if (not fname.isEmpty()) and QFile.exists(fname):
                print "TODO: implement file loading"
                #ok, msg = self.annotations.load(fname)
                #self.updateStatus(msg)
                #self.updateViews()

    def okToContinue(self):
        return True
        if self.annotations.dirty():
            reply = QMessageBox.question(self,
                    "%s - Unsaved Changes" % (APP_NAME),
                    "Save unsaved changes?",
                    QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                print "TODO: implement file saving"
        return True

    def fileNew(self):
        if not self.okToContinue():
            return
        #self.annotations.clear()
        #self.updateStatus()
        #self.updateViews()

    def fileOpen(self):
        print "TODO: implement fileOpen"
        return False

        if not self.okToContinue():
            return
        path = '.'
        if (self.annotations.filename() is not None) and \
                (len(self.annotations.filename()) > 0):
            path = QFileInfo(self.annotations.filename()).path()

        format_str = ' '.join(['*.'+fmt for fmt in self.annotations.formats()])
        fname = QFileDialog.getOpenFileName(self, 
                "%s - Load Annotations" % APP_NAME, path,
                "%s annotation files (%s)" % (APP_NAME, format_str))
        if not fname.isEmpty():
            ok, msg = self.annotations.load(fname)
            self.updateStatus(msg)
            self.updateViews()

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
        format_str = ' '.join(['*.'+fmt for fmt in self.annotations.formats()])
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

    ##______________________________________________________________________________
    ## global event handling

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

