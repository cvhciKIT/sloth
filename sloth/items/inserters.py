from PyQt4.QtGui import *
from PyQt4.Qt import *
import math

class ItemInserter(QObject):
    # Signals
    inserterFinished = pyqtSignal()

    def __init__(self, labeltool, scene, default_properties=None):
        QObject.__init__(self)
        self.labeltool_          = labeltool
        self.scene_              = scene
        self.default_properties_ = default_properties

    def mousePressEvent(self, event, image_item):
        event.accept()

    def mouseReleaseEvent(self, event, image_item):
        event.accept()

    def mouseMoveEvent(self, event, image_item):
        event.accept()

    def keyPressEvent(self, event, image_item):
        event.ignore()

    def allowOutOfSceneEvents(self):
        return False

    def abort(self):
        self.inserterFinished.emit()

class PointItemInserter(ItemInserter):
    def mousePressEvent(self, event, image_item):
        pos = event.scenePos()
        ann = {'x': pos.x(), 'y': pos.y()}
        ann.update(self.default_properties_)
        image_item.addAnnotation(ann)
        event.accept()

class RectItemInserter(ItemInserter):
    def __init__(self, labeltool, scene, default_properties=None):
        ItemInserter.__init__(self, labeltool, scene, default_properties)
        self.current_item_ = None
        self.init_pos_     = None

    def mousePressEvent(self, event, image_item):
        pos = event.scenePos()
        item = QGraphicsRectItem(QRectF(pos.x(), pos.y(), 0, 0))
        item.setPen(Qt.red)
        self.current_item_ = item
        self.init_pos_     = pos
        self.scene_.addItem(item)
        event.accept()

    def mouseMoveEvent(self, event, image_item):
        if self.current_item_ is not None:
            assert self.init_pos_ is not None
            rect = QRectF(self.init_pos_, event.scenePos()).normalized()
            self.current_item_.setRect(rect)

        event.accept()

    def mouseReleaseEvent(self, event, image_item):
        if self.current_item_ is not None:
            if self.current_item_.rect().width() > 1 and \
               self.current_item_.rect().height() > 1:
                rect = self.current_item_.rect()
                ann = {'x': rect.x(), 'y': rect.y(),
                       'width': rect.width(), 'height': rect.height()}
                ann.update(self.default_properties_)
                image_item.addAnnotation(ann)
            self.scene_.removeItem(self.current_item_)
            self.current_item_ = None
            self.init_pos_ = None

        event.accept()

    def allowOutOfSceneEvents(self):
        return True

    def abort(self):
        if self.current_item_ is not None:
            self.scene_.removeItem(self.current_item_)
            self.current_item_ = None
            self.init_pos_ = None
        ItemInserter.abort(self)

class FixedRatioRectItemInserter(RectItemInserter):
    def __init__(self, labeltool, scene, default_properties=None):
        RectItemInserter.__init__(self, labeltool, scene, default_properties)
        self.ratio_ = 1
        if default_properties is not None:
            self.ratio_ = float(default_properties.get('_ratio', 1))

    def mouseMoveEvent(self, event, image_item):
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

# TODO
class PolygonItemInserter(ItemInserter):
    def __init__(self, scene, mode=None):
        ItemInserter.__init__(self, scene, mode)
        self.current_item_ = None

    def mousePressEvent(self, event, image_item):
        pos = event.scenePos()
        if self.current_item_ is None:
            item = QGraphicsPolygonItem(QPolygonF([pos]))
            self.current_item_ = item
            self.scene_.addItem(item)
        else:
            polygon = self.current_item_.polygon()
            polygon.append(pos)
            self.current_item_.setPolygon(polygon)

        event.accept()

    def mouseMoveEvent(self, event, image_item):
        if self.current_item_ is not None:
            pos = event.scenePos()
            polygon = self.current_item_.polygon()
            assert polygon.size() > 0
            polygon[-1] = pos
            self.current_item_.setPolygon(polygon)

        event.accept()

