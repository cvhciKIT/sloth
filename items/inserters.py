from PyQt4.QtGui import *
from PyQt4.Qt import *
import math

class ItemInserter:
    def __init__(self, scene, mode=None):
        self.scene_ = scene
        self.mode_  = mode

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

    def keyPressEvent(self, event, index):
        event.ignore()

class PointItemInserter(ItemInserter):
    def mousePressEvent(self, event, index):
        pos = event.scenePos()
        ann = {'type': 'point',
               'x': pos.x(), 'y': pos.y()}
        index.model().addAnnotation(index, ann)
        event.accept()

class RectItemInserter(ItemInserter):
    def __init__(self, scene, mode=None):
        ItemInserter.__init__(self, scene, mode)
        self.current_item_ = None
        self.init_pos_ = None

    def mousePressEvent(self, event, index):
        pos = event.scenePos()
        item = QGraphicsRectItem(QRectF(pos.x(), pos.y(), 0, 0))
        item.setPen(Qt.red)
        self.current_item_ = item
        self.init_pos_     = pos
        self.scene().addItem(item)
        event.accept()

    def mouseMoveEvent(self, event, index):
        if self.current_item_ is not None:
            assert self.init_pos_ is not None
            rect = QRectF(self.init_pos_, event.scenePos()).normalized()
            self.current_item_.setRect(rect)

        event.accept()

    def mouseReleaseEvent(self, event, index):
        if self.current_item_ is not None:
            if self.current_item_.rect().width() > 1 and \
               self.current_item_.rect().height() > 1:
                rect = self.current_item_.rect()
                ann = {'type': 'rect',
                       'x': rect.x(), 'y': rect.y(),
                       'width': rect.width(), 'height': rect.height()}
                index.model().addAnnotation(index, ann)
            self.scene().removeItem(self.current_item_)
            self.current_item_ = None
            self.init_pos_ = None

        event.accept()

class FixedRatioRectItemInserter(RectItemInserter):
    def __init__(self, scene, mode=None):
        RectItemInserter.__init__(self, scene, mode)
        self.ratio_ = 1
        if mode is not None:
            self.ratio_ = float(mode.get('_ratio', 1))

    def setMode(self, mode):
        if mode is not None:
            self.ratio_ = float(mode.get('_ratio', 1))
        RectItemInserter.setMode(self, mode)

    def mouseMoveEvent(self, event, index):
        if self.current_item_ is not None:
            new_geometry = QRectF(self.current_item_.rect().topLeft(), event.scenePos())
            dx = new_geometry.width()
            dy = new_geometry.height()
            d = math.sqrt(dx*dx + dy*dy)
            r = self.ratio_
            k = math.sqrt(r*r+1)
            h = d/k
            w = d*r/k
            new_geometry.setWidth(w)
            new_geometry.setHeight(h)
            self.current_item_.setRect(new_geometry.normalized())

        event.accept()

class PolygonItemInserter(ItemInserter):
    def __init__(self, scene, mode=None):
        ItemInserter.__init__(self, scene, mode)
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

