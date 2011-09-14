from PyQt4.QtGui import *
from PyQt4.QtCore import *

class CopyAnnotationsPlugin(QObject):
    def __init__(self, labeltool):
        QObject.__init__(self)
        self._labeltool = labeltool
        self._wnd = labeltool.mainWindow()
        self._sc  = QAction("Copy labels from previous image/frame", self._wnd)
        self._sc.triggered.connect(self.copy)

    def copy(self):
        current = self._labeltool.currentImage()
        if current is not None:
            prev = current.getPreviousSibling()
            if prev is not None:
                for annotation in prev.children():
                    copied = dict(annotation.iteritems())
                    current.addAnnotation(copied)

    def action(self):
        return self._sc
