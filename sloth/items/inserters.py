import math
from PyQt4.QtGui import *
from PyQt4.Qt import *


class ItemInserter(QObject):
    """
    The base class for all item insertion handlers.
    """
    # Signals
    annotationFinished = pyqtSignal()
    inserterFinished = pyqtSignal()

    def __init__(self, labeltool, scene, default_properties=None,
                 prefix="", commit=True):
        QObject.__init__(self)
        self._labeltool = labeltool
        self._scene = scene
        self._default_properties = default_properties or {}
        self._prefix = prefix
        self._ann = {}
        self._commit = commit
        self._item = None
        self._pen = Qt.red

    def annotation(self):
        return self._ann

    def item(self):
        return self._item

    def pen(self):
        return self._pen

    def setPen(self, pen):
        self._pen = pen

    def mousePressEvent(self, event, image_item):
        event.accept()

    def mouseDoubleClickEvent(self, event, image_item):
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
        self._ann.update({
            self._prefix + 'x': pos.x(),
            self._prefix + 'y': pos.y()})
        self._ann.update(self._default_properties)
        if self._commit:
            image_item.addAnnotation(self._ann)
        self._item = QGraphicsEllipseItem(QRectF(pos.x() - 2,
                                          pos.y() - 2, 5, 5))
        self._item.setPen(self.pen())
        self.annotationFinished.emit()
        event.accept()


class RectItemInserter(ItemInserter):
    def __init__(self, labeltool, scene, default_properties=None,
                 prefix="", commit=True):
        ItemInserter.__init__(self, labeltool, scene, default_properties,
                              prefix, commit)
        self._aiming = True
        self._helpLines = None
        self._helpLinesPen = QPen(Qt.green, 2, Qt.DashLine)
        self._init_pos = None

    def mousePressEvent(self, event, image_item):
        self._aiming = False
        if self._helpLines is not None:
            self._scene.removeItem(self._helpLines)
            self._helpLines = None

        pos = event.scenePos()
        self._init_pos = pos
        self._item = QGraphicsRectItem(QRectF(pos.x(), pos.y(), 0, 0))
        self._item.setPen(self.pen())
        self._scene.addItem(self._item)
        event.accept()

    def mouseMoveEvent(self, event, image_item):
        if self._aiming:
            if self._helpLines is not None:
                self._scene.removeItem(self._helpLines)

            self._helpLines = QGraphicsItemGroup()
            group = self._helpLines

            verticalHelpLine = QGraphicsLineItem(event.scenePos().x(), 0, event.scenePos().x(), self._scene.height())
            horizontalHelpLine = QGraphicsLineItem(0, event.scenePos().y(), self._scene.width(), event.scenePos().y())

            horizontalHelpLine.setPen(self._helpLinesPen)
            verticalHelpLine.setPen(self._helpLinesPen)

            group.addToGroup(verticalHelpLine);
            group.addToGroup(horizontalHelpLine);

            self._scene.addItem(self._helpLines)
        else:
            if self._item is not None:
                assert self._init_pos is not None
                rect = QRectF(self._init_pos, event.scenePos()).normalized()
                self._item.setRect(rect)

        event.accept()

    def mouseReleaseEvent(self, event, image_item):
        if self._item is not None:
            if self._item.rect().width() > 1 and \
               self._item.rect().height() > 1:
                rect = self._item.rect()
                self._ann.update({self._prefix + 'x': rect.x(),
                                  self._prefix + 'y': rect.y(),
                                  self._prefix + 'width': rect.width(),
                                  self._prefix + 'height': rect.height()})
                self._ann.update(self._default_properties)
                if self._commit:
                    image_item.addAnnotation(self._ann)
            self._scene.removeItem(self._item)
            self.annotationFinished.emit()
            self._init_pos = None
            self._item = None

        self._aiming = True
        self._scene.views()[0].viewport().setCursor(Qt.CrossCursor)
        event.accept()

    def allowOutOfSceneEvents(self):
        return True

    def abort(self):
        if self._helpLines is not None:
            self._scene.removeItem(self._helpLines)
            self._helpLines = None

        if self._item is not None:
            self._scene.removeItem(self._item)
            self._item = None
            self._init_pos = None
        ItemInserter.abort(self)


class FixedRatioRectItemInserter(RectItemInserter):
    def __init__(self, labeltool, scene, default_properties=None,
                 prefix="", commit=True):
        RectItemInserter.__init__(self, labeltool, scene, default_properties,
                                  prefix, commit)
        self._ratio = float(default_properties.get('_ratio', 1))

    def mouseMoveEvent(self, event, image_item):
        if self._current_item is not None:
            new_geometry = QRectF(self._current_item.rect().topLeft(),
                                  event.scenePos())
            dx = new_geometry.width()
            dy = new_geometry.height()
            d = math.sqrt(dx * dx + dy * dy)
            r = self._ratio
            k = math.sqrt(r * r + 1)
            h = d / k
            w = d * r / k
            new_geometry.setWidth(w)
            new_geometry.setHeight(h)
            self._current_item.setRect(new_geometry.normalized())

        event.accept()


class SequenceItemInserter(ItemInserter):
    inserters = []

    def __init__(self, labeltool, scene, default_properties=None,
                 prefix="", commit=True):
        ItemInserter.__init__(self, labeltool, scene, default_properties,
                              prefix, commit)
        self._items = []
        self._state = 0
        self._current_inserter = None
        self._current_image_item = None

        self.nextState(0)

    def _cleanup(self):
        for item in self._items:
            if item.scene() is not None:
                self._scene.removeItem(item)
        self._items = []
        self._scene.clearMessage()
        self._current_inserter = None

    def updateAnnotation(self, ann):
        self._ann.update(ann)

    def nextState(self, next_state=None):
        if next_state is None:
            next_state = self._state + 1

        if self._current_inserter is not None:
            self.updateAnnotation(self._current_inserter.annotation())
            item = self._current_inserter.item()
            if item is not None:
                self._scene.addItem(item)
                self._items.append(item)

            self._current_inserter.annotationFinished.disconnect(self.nextState)

            if next_state >= len(self.inserters):
                self._ann.update(self._default_properties)
                if self._commit:
                    self._current_image_item.addAnnotation(self._ann)
                self.annotationFinished.emit()
                self._cleanup()
                next_state = 0

        callable_, prefix, message = self.inserters[next_state]
        self._current_inserter = callable_(self._labeltool, self._scene,
                                           prefix=prefix, commit=False)
        self._current_inserter.annotationFinished.connect(self.nextState)
        if message:
            self._scene.setMessage(message)
        else:
            self._scene.clearMessage()
        self._state = next_state

    def mousePressEvent(self, event, image_item):
        self._current_image_item = image_item
        self._current_inserter.mousePressEvent(event, image_item)

    def mouseMoveEvent(self, event, image_item):
        self._current_image_item = image_item
        self._current_inserter.mouseMoveEvent(event, image_item)

    def mouseReleaseEvent(self, event, image_item):
        self._current_image_item = image_item
        self._current_inserter.mouseReleaseEvent(event, image_item)

    def keyPressEvent(self, event, image_item):
        self._current_image_item = image_item
        self._current_inserter.keyPressEvent(event, image_item)

    def abort(self):
        self._cleanup()
        self.inserterFinished.emit()


class BBoxFaceInserter(SequenceItemInserter):
    inserters = [
        (RectItemInserter,  "bbox", "Labelling bounding box"),
        (PointItemInserter, "lec",  "Labelling left eye center"),
        (PointItemInserter, "rec",  "Labelling right eye center"),
        (PointItemInserter, "mc",   "Labelling mouth center"),
    ]

    def toggleOccludedForCurrentInserter(self):
        if self._state > 0:
            prefix = self.inserters[self._state][1]
            occluded = not self._current_inserter._ann.get(prefix + 'occluded', False)
            self._current_inserter._ann[prefix + 'occluded'] = occluded
            if occluded:
                self._scene.setMessage(self.inserters[self._state][2] + ' (occluded)')
            else:
                self._scene.setMessage(self.inserters[self._state][2])

    def mousePressEvent(self, event, image_item):
        if event.buttons() & Qt.RightButton:
            self.toggleOccludedForCurrentInserter()
        SequenceItemInserter.mousePressEvent(self, event, image_item)

    def keyPressEvent(self, event, image_item):
        if event.key() == Qt.Key_O and self._state > 0:
            self.toggleOccludedForCurrentInserter()
            return
        elif Qt.Key_0 <= event.key() <= Qt.Key_9 or Qt.Key_A <= event.key() <= Qt.Key_Z:
            if Qt.Key_0 <= event.key() <= Qt.Key_9:
                self._ann['id'] = int(str(event.text()))
            else:
                self._ann['id'] = ord(str(event.text()).upper()) - 65 + 10
            message = self._scene._message
            if message is None:
                message = ""
            self._scene.setMessage(message + "\nSet id to %d." % self._ann['id'])
            return
        SequenceItemInserter.keyPressEvent(self, event, image_item)

    def imageChange(self):
        if self._state > 0:
            # restart the inserter
            self._cleanup()
            self.nextState(0)
            self._scene.setMessage("<b>Warning</b>: Image changed during insert operation.\n" +
                                   "Resetting the inserter state.\n" +
                                   "Now at: " + self.inserters[self._state][2])


class NPointFaceInserter(SequenceItemInserter):
    inserters = [
            (PointItemInserter, "leoc", "left eye outer corner"),
            (PointItemInserter, "leic", "left eye inner corner"),
            (PointItemInserter, "reic", "right eye inner corner"),
            (PointItemInserter, "reoc", "right eye outer corner"),
            (PointItemInserter, "nt",   "nose tip"),
            (PointItemInserter, "ulc",  "upper lip center"),
    ]

    def toggleOccludedForCurrentInserter(self):
        prefix = self.inserters[self._state][1]
        occluded = not self._current_inserter._ann.get(prefix + 'occluded', False)
        self._current_inserter._ann[prefix + 'occluded'] = occluded
        if occluded:
            self._scene.setMessage(self.inserters[self._state][2] + ' (occluded)')
            self._current_inserter.setPen(Qt.red)
        else:
            self._scene.setMessage(self.inserters[self._state][2])
            self._current_inserter.setPen(Qt.yellow)

    def mousePressEvent(self, event, image_item):
        if event.buttons() & Qt.RightButton:
            self.toggleOccludedForCurrentInserter()
        SequenceItemInserter.mousePressEvent(self, event, image_item)

    def keyPressEvent(self, event, image_item):
        if event.key() == Qt.Key_O:
            self.toggleOccludedForCurrentInserter()
        SequenceItemInserter.keyPressEvent(self, event, image_item)

    def imageChange(self):
        if self._state > 0:
            # restart the inserter
            self._cleanup()
            self.nextState(0)
            self._scene.setMessage("<b>Warning</b>: Image changed during insert operation.\n" +
                                   "Resetting the inserter state.\n" +
                                   "Now at: " + self.inserters[self._state][2])


class PolygonItemInserter(ItemInserter):
    def __init__(self, labeltool, scene, default_properties=None,
                 prefix="", commit=True):
        ItemInserter.__init__(self, labeltool, scene, default_properties,
                              prefix, commit)
        self._item = None

    def _removeLastPointAndFinish(self, image_item):
        polygon = self._item.polygon()
        polygon.remove(polygon.size()-1)
        assert polygon.size() > 0
        self._item.setPolygon(polygon)

        self._updateAnnotation()
        if self._commit:
            image_item.addAnnotation(self._ann)
        self._scene.removeItem(self._item)
        self.annotationFinished.emit()
        self._item = None
        self._scene.clearMessage()

        self.inserterFinished.emit()

    def mousePressEvent(self, event, image_item):
        pos = event.scenePos()

        if self._item is None:
            item = QGraphicsPolygonItem(QPolygonF([pos]))
            self._item = item
            self._item.setPen(self.pen())
            self._scene.addItem(item)

            self._scene.setMessage("Press Enter to finish the polygon.")

        polygon = self._item.polygon()
        polygon.append(pos)
        self._item.setPolygon(polygon)

        event.accept()

    def mouseDoubleClickEvent(self, event, image_item):
        """Finish the polygon when the user double clicks."""

        # No need to add the position of the click, as a single mouse
        # press event added the point already.
        # Even then, the last point of the polygon is duplicate as it would be
        # shortly after a single mouse press. At this point, we want to throw it
        # away.
        self._removeLastPointAndFinish(image_item)

        event.accept()


    def mouseMoveEvent(self, event, image_item):
        if self._item is not None:
            pos = event.scenePos()
            polygon = self._item.polygon()
            assert polygon.size() > 0
            polygon[-1] = pos
            self._item.setPolygon(polygon)

        event.accept()

    def keyPressEvent(self, event, image_item):
        """
        When the user presses Enter, the polygon is finished.
        """
        if event.key() == Qt.Key_Return and self._item is not None:
            # The last point of the polygon is the point the user would add
            # to the polygon when pressing the mouse button. At this point,
            # we want to throw it away.
            self._removeLastPointAndFinish(image_item)

    def abort(self):
        if self._item is not None:
            self._scene.removeItem(self._item)
            self._item = None
            self._scene.clearMessage()
        ItemInserter.abort(self)

    def _updateAnnotation(self):
        polygon = self._item.polygon()
        self._ann.update({self._prefix + 'xn':
                              ";".join([str(p.x()) for p in polygon]),
                          self._prefix + 'yn':
                              ";".join([str(p.y()) for p in polygon])})
        self._ann.update(self._default_properties)
