from PyQt4.QtGui import *
from PyQt4.QtCore import *
from sceneitems import *
import math

class ItemInserter:
    def __init__(self, scene, model=None):
        self.scene_ = scene
        self.model_ = model
        self.mode_  = None

    def setModel(self, model):
        self.model_ = model
    def model(self):
        return self.model_

    def setScene(self, scene):
        self.scene_ = scene
    def scene(self):
        return self.scene_

    def setMode(self, mode):
        self.mode_  = mode
    def mode(self):
        return self.mode

    def mousePressEvent(self, event, index):
        event.accept()

    def mouseReleaseEvent(self, event, index):
        event.accept()

    def mouseMoveEvent(self, event, index):
        event.accept()

class PointItemInserter(ItemInserter):
    def mousePressEvent(self, event, index):
        pos = event.scenePos()
        # TODO create it in the model instead
        item = QGraphicsEllipseItem(QRectF(pos.x()-1, pos.y()-1, 2, 2))
        self.scene().addItem(item)

        event.accept()

class RectItemInserter(ItemInserter):
    def __init__(self, scene, model=None):
        ItemInserter.__init__(self, scene, model)
        self.current_item_ = None
        self.init_pos_ = None

    def mousePressEvent(self, event, index):
        pos = event.scenePos()
        # TODO create it in the model instead
        item = QGraphicsRectItem(QRectF(pos.x(), pos.y(), 0, 0))
        self.current_item_ = item
        self.init_pos_     = pos
        self.scene().addItem(item)

        event.accept()

    def mouseMoveEvent(self, event, index):
        if self.current_item_ is not None:
            assert self.init_pos_ is not None
            pos = event.scenePos()
            rect = QRectF(self.init_pos_.x(), self.init_pos_.y(),
                          pos.x() - self.init_pos_.x(), pos.y() - self.init_pos_.y())
            self.current_item_.setRect(rect.normalized())

        event.accept()

    def mouseReleaseEvent(self, event, index):
        if self.current_item_ is not None:
            if self.current_item_.rect().width() > 1 and \
               self.current_item_.rect().height() > 1:
                # TODO commit to the model
                print "added rect:", self.current_item_
            self.current_item_ = None
            self.init_pos_ = None

        event.accept()

class PolygonItemInserter(ItemInserter):
    def __init__(self, scene, model=None):
        ItemInserter.__init__(self, scene, model)
        self.current_item_ = None

    def mousePressEvent(self, event, index):
        pos = event.scenePos()
        if self.current_item_ is None:
            item = QGraphicsPolygonItem(QPolygonF([pos]))
            self.current_item_ = item
            self.scene().addItem(item)
        else:
            polygon = self.current_item_.polygon()
            polygon.append(pos)
            self.current_item_.setPolygon(polygon)

        event.accept()

    def mouseMoveEvent(self, event, index):
        if self.current_item_ is not None:
            pos = event.scenePos()
            polygon = self.current_item_.polygon()
            assert polygon.size() > 0
            polygon[-1] = pos
            self.current_item_.setPolygon(polygon)

        event.accept()

class AnnotationScene(QGraphicsScene):

    # TODO signal itemadded

    def __init__(self, parent=None):
        super(AnnotationScene, self).__init__(parent)
        self.setBackgroundBrush(Qt.darkGray)

        self.reset()
        self.setSceneRect(0,0, 640, 480)
        self.addRect(QRectF(0, 0, 640, 480), brush=Qt.white)

        self.mode_         = None
        self.inserters_    = {}
        self.inserter_     = None
        self.debug_ = True

        self.addItemInserter('point', PointItemInserter(self))
        self.addItemInserter('rect',  RectItemInserter(self))
        self.addItemInserter('poly',  PolygonItemInserter(self))
        self.addItemInserter('polygon',  PolygonItemInserter(self))

        #self.setMode({'type': 'point'})
        #self.setMode({'type': 'rect'})
        self.setMode({'type': 'poly'})

    def reset(self):
        self.clear()

    def setMode(self, mode):
        print "setMode :", mode
        self.mode_ = mode

        if self.mode_ == None:
            self.inserter_ = None
            return

        if not self.mode_['type'] in self.inserters_:
            raise InvalidArgumentException("Invalid mode")

        self.inserter_ = self.inserters_[self.mode_['type']]
        self.inserter_.setMode(self.mode_)

    def addItemInserter(self, type, inserter):
        if type in self.inserters_:
            raise Exception("Type %s already has an inserter" % type)

        self.inserters_[type] = inserter

    def removeItemInserter(self, type):
        if type in self.inserters_:
            del self.inserters_[type]

    def mousePressEvent(self, event):
        if self.debug_:
            print "mousePressEvent", self.sceneRect().contains(event.scenePos()), event.scenePos()
        if not self.sceneRect().contains(event.scenePos()):
            # ignore events outside the scene rect
            return
        elif self.inserter_ is not None:
            # insert mode
            self.inserter_.mousePressEvent(event, None)
        else:
            # selection mode
            QGraphicsScene.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.debug_:
            print "mouseReleaseEvent", self.sceneRect().contains(event.scenePos()), event.scenePos()
        if self.inserter_ is not None:
            # insert mode
            self.inserter_.mouseReleaseEvent(event, None)
        else:
            # selection mode
            QGraphicsScene.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.debug_:
            print "mouseMoveEvent", self.sceneRect().contains(event.scenePos()), event.scenePos()
        if self.inserter_ is not None:
            # insert mode
            self.inserter_.mouseMoveEvent(event, None)
        else:
            # selection mode
            QGraphicsScene.mouseMoveEvent(self, event)

    def addItem(self, item):
        QGraphicsScene.addItem(self, item)
        # TODO emit signal itemAdded

