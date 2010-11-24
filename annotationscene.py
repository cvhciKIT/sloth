from PyQt4.QtGui import *
from PyQt4.QtCore import *
from pointitem import *
import math

modes = range(5)
SELECT, POINT, LINE, RECTANGLE, POLYGON = modes

class AnnotationScene(QGraphicsScene):
    def __init__(self, parent=None):
        super(AnnotationScene, self).__init__(parent)
        self.setBackgroundBrush(Qt.darkGray)

        self.reset()
        self.setSceneRect(0,0, 640, 480)

        self.mode_ = None
        self.mousePressed_ = None
        self.activeItem_ = None

    def reset(self):
        self.clear()

    def setMode(self, mode):
        assert (mode in modes)
        self.mode_ = mode
        print mode
    
        
    def mousePressEvent(self, event):
        if not self.sceneRect().contains(event.scenePos()):
            return
        elif self.mode_ == SELECT:
            QGraphicsScene.mousePressEvent(self, event)
            return
        elif self.mode_ == POINT:
            self.insertItem(AnnotationGraphicsPointItem(event.scenePos()))
            event.accept()
        elif self.mode_ == LINE:
            self.mousePressed_ = event.scenePos()
            line = QGraphicsLineItem(QLineF(event.scenePos(), event.scenePos()))
            self.activeItem_ = line
            self.addItem(line)

            event.accept()
        self.update()

    def mouseReleaseEvent(self, event):
        self.mousePressed_ = None
        QGraphicsScene.mouseReleaseEvent(self, event)
        
    def mouseMoveEvent(self, event):
        print LINE
        if not self.sceneRect().contains(event.scenePos()):
            return
        elif self.mode_ == LINE:
            ## TODO
            activeItem.
        else:
            QGraphicsScene.mouseMoveEvent(self, event)

    def insertItem(self, item):
        self.addItem(item)
