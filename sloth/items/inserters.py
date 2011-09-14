from PyQt4.QtGui import *
from PyQt4.Qt import *
import math

class ItemInserter(QObject):
    """
    The base class for all item insertion handlers.
    """
    # Signals
    annotationFinished = pyqtSignal()
    inserterFinished   = pyqtSignal()

    def __init__(self, labeltool, scene, default_properties=None, prefix="", commit=True):
        QObject.__init__(self)
        self._labeltool          = labeltool
        self._scene              = scene
        self._default_properties = default_properties
        self._prefix             = prefix
        self._ann                = {}
        if default_properties is not None:
            self._ann = dict(self._default_properties.iteritems())
        self._commit             = commit
        self._item               = None

    def annotation(self):
        return self._ann

    def item(self):
        return self._item

    def pen(self):
        return Qt.red

    def mousePressEvent(self, event, image_item):
        event.accept()

    def mouseReleaseEvent(self, event, image_item):
        event.accept()

    def mouseMoveEvent(self, event, image_item):
        event.accept()

    def keyPressEvent(self, event, image_item):
        event.ignore()

    def imageChange(self):
        """
        Slot which gets called if the current image in the labeltool changes.
        """
        pass

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

class NPointFaceInserter(ItemInserter):
    landmarks = [
            ("leoc", "left eye outer corner"),
            ("leic", "left eye inner corner"),
            ("reic", "right eye inner corner"),
            ("reoc", "right eye outer corner"),
            ("nt",   "nose tip"),
            ("mlc",  "left mouth corner"),
            ("mrc",  "right mouth corner"),
            ]

    def __init__(self, labeltool, scene, default_properties=None):
        ItemInserter.__init__(self, labeltool, scene, default_properties)
        self._reset()

    def _reset(self):
        self._state = 0
        self._items = []
        self._values = {}
        self._image_item = None
        self._scene.setMessage("Labeling %s" % self.landmarks[self._state][1])
        pass

    def _cleanup(self):
        for item in self._items:
            self._scene.removeItem(item)
        self._scene.clearMessage()

    def _insertItem(self):
        item = {}
        item.update(self._default_properties)
        item.update(self._values)
        self._image_item.addAnnotation(item)

    def mousePressEvent(self, event, image_item):
        if self._image_item is None:
            self._image_item = image_item
        else:
            assert(self._image_item == image_item)

        pos = event.scenePos()
        if event.buttons() & Qt.LeftButton:
            self._values[self.landmarks[self._state][0] + "x"] = pos.x()
            self._values[self.landmarks[self._state][0] + "y"] = pos.y()
            item = QGraphicsEllipseItem(QRectF(pos.x()-2, pos.y()-2, 5, 5))
            item.setPen(Qt.red)
            self._scene.addItem(item)
            self._items.append(item)
        else:
            self._values[self.landmarks[self._state][0] + "x"] = -1
            self._values[self.landmarks[self._state][0] + "y"] = -1

        if self._state == len(self.landmarks)-1:
            self._cleanup()
            self._insertItem()
            self.inserterFinished.emit()
        else:
            self._state += 1
            self._scene.setMessage("Labeling %s" % self.landmarks[self._state][1])

    def abort(self):
        self._cleanup()
        self.inserterFinished.emit()

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

