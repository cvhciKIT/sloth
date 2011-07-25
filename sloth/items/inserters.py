from PyQt4.QtGui import *
from PyQt4.Qt import *
import math

class ItemInserter(QObject):
    # Signals
    inserterFinished = pyqtSignal()

    def __init__(self, labeltool, scene, default_properties=None):
        QObject.__init__(self)
        self._labeltool          = labeltool
        self._scene              = scene
        self._default_properties = default_properties

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
        ann.update(self._default_properties)
        image_item.addAnnotation(ann)
        event.accept()

class RectItemInserter(ItemInserter):
    def __init__(self, labeltool, scene, default_properties=None):
        ItemInserter.__init__(self, labeltool, scene, default_properties)
        self._current_item = None
        self._init_pos     = None

    def mousePressEvent(self, event, image_item):
        pos = event.scenePos()
        item = QGraphicsRectItem(QRectF(pos.x(), pos.y(), 0, 0))
        item.setPen(Qt.red)
        self._current_item = item
        self._init_pos     = pos
        self._scene.addItem(item)
        event.accept()

    def mouseMoveEvent(self, event, image_item):
        if self._current_item is not None:
            assert self._init_pos is not None
            rect = QRectF(self._init_pos, event.scenePos()).normalized()
            self._current_item.setRect(rect)

        event.accept()

    def mouseReleaseEvent(self, event, image_item):
        if self._current_item is not None:
            if self._current_item.rect().width() > 1 and \
               self._current_item.rect().height() > 1:
                rect = self._current_item.rect()
                ann = {'x': rect.x(), 'y': rect.y(),
                       'width': rect.width(), 'height': rect.height()}
                ann.update(self._default_properties)
                image_item.addAnnotation(ann)
            self._scene.removeItem(self._current_item)
            self._current_item = None
            self._init_pos = None

        event.accept()

    def allowOutOfSceneEvents(self):
        return True

    def abort(self):
        if self._current_item is not None:
            self._scene.removeItem(self._current_item)
            self._current_item = None
            self._init_pos = None
        ItemInserter.abort(self)

class FixedRatioRectItemInserter(RectItemInserter):
    def __init__(self, labeltool, scene, default_properties=None):
        RectItemInserter.__init__(self, labeltool, scene, default_properties)
        self._ratio = 1
        if default_properties is not None:
            self._ratio = float(default_properties.get('_ratio', 1))

    def mouseMoveEvent(self, event, image_item):
        if self._current_item is not None:
            new_geometry = QRectF(self._current_item.rect().topLeft(), event.scenePos())
            dx = new_geometry.width()
            dy = new_geometry.height()
            d = math.sqrt(dx*dx + dy*dy)
            r = self._ratio
            k = math.sqrt(r*r+1)
            h = d/k
            w = d*r/k
            new_geometry.setWidth(w)
            new_geometry.setHeight(h)
            self._current_item.setRect(new_geometry.normalized())

        event.accept()

# TODO
class PolygonItemInserter(ItemInserter):
    def __init__(self, scene, mode=None):
        ItemInserter.__init__(self, scene, mode)
        self._current_item = None

    def mousePressEvent(self, event, image_item):
        pos = event.scenePos()
        if self._current_item is None:
            item = QGraphicsPolygonItem(QPolygonF([pos]))
            self._current_item = item
            self._scene.addItem(item)
        else:
            polygon = self._current_item.polygon()
            polygon.append(pos)
            self._current_item.setPolygon(polygon)

        event.accept()

    def mouseMoveEvent(self, event, image_item):
        if self._current_item is not None:
            pos = event.scenePos()
            polygon = self._current_item.polygon()
            assert polygon.size() > 0
            polygon[-1] = pos
            self._current_item.setPolygon(polygon)

        event.accept()

