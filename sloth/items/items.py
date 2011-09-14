from PyQt4.QtGui import *
from PyQt4.Qt import *

import logging
LOG = logging.getLogger(__name__)

class BaseItem(QAbstractGraphicsShapeItem):
    """
    Base class for visualization items.
    """

    def __init__(self, model_item=None, prefix="", parent=None):
        """
        Creates a visualization item.

        Parameters
        ==========
        index :
        data :
        parent :
        """
        QAbstractGraphicsShapeItem.__init__(self, parent)
        self.setFlags(QGraphicsItem.ItemIsSelectable | \
                      QGraphicsItem.ItemIsMovable | \
                      QGraphicsItem.ItemSendsGeometryChanges | \
                      QGraphicsItem.ItemSendsScenePositionChanges)

        self._model_item = model_item
        if self._model_item is not None:
            self._model_item.model().dataChanged.connect(self.onDataChanged)

        self.changeColor()

        # initialize members
        self._prefix = prefix
        self._text = ""
        self._text_bg_brush = None
        self._auto_text_keys = []

    def changeColor(self):
        if self._model_item is not None:
            c = self._model_item.getColor()
            if c is not None:
                self.setColor(c)
                return
        self.setColor(Qt.yellow)

    def onDataChanged(self, indexFrom, indexTo):
        if indexFrom == self._model_item.index():
            self.changeColor()

    def modelItem(self):
        """
        Returns the model item of this items.
        """
        return self._model_item

    def index(self):
        """
        Returns the index of this item.
        """
        return self._model_item.index()

    def prefix(self):
        """
        Returns the key prefix of the item.
        """
        return self._prefix

    def setText(self, text=""):
        """
        Sets a text to be displayed on this item.
        """
        self._text = text

    def text(self):
        return self._text

    def setTextBackgroundBrush(self, brush=None):
        """
        Sets the brush to be used to fill the background region
        behind the text. Set to None to not draw a background
        (leave transparent).
        """
        self._text_bg_brush = brush

    def textBackgroundBrush(self):
        """
        Returns the background brush for the text region.
        """
        return self._text_bg_brush

    def setAutoTextKeys(self, keys=[]):
        """
        Sets the keys for which the values from the annotations
        are displayed automatically as text.
        """
        self._auto_text_keys = keys

    def autoTextKeys(self):
        """
        Returns the list of keys for which the values from
        the annotations are displayed as text automatically.
        """
        return self._auto_text_keys

    def _compile_text(self):
        text_lines = []
        if self._text != "" and self._text is not None:
            text_lines.append(self._text)
        for key in self._auto_text_keys:
            text_lines.append("%s: %s" % \
                    (key, self._model_item.get(key, "")))
        return '\n'.join(text_lines)

    def dataChanged(self):
        self.dataChange()
        self.update()

    def dataChange(self):
        pass

    def updateModel(self, ann=None):
        if ann is not None:
            self._model_item.update(ann)

    def paint(self, painter, option, widget=None):
        painter.save()
        painter.setPen(self.pen())

        # display the text for this item
        text = self._compile_text()
        rect = painter.boundingRect(
                QRect(5, 5, 1000, 1000), Qt.AlignTop | Qt.AlignLeft, text)

        # fill background region behind text
        if self._text_bg_brush is not None:
            bg_rect = rect.adjusted(-3, -3, 3, 3)
            painter.fillRect(bg_rect, self._text_bg_brush)

        painter.drawText(rect, Qt.AlignTop | Qt.AlignLeft, text)
        painter.restore()

    def boundingRect(self):
        return QRectF(0, 0, 0, 0)

    def setColor(self, color):
        self.setPen(color)
        self.setBrush(color)
        self.update()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.updateModel()
        return QAbstractGraphicsShapeItem.itemChange(self, change, value)


class PointItem(BaseItem):
    """
    Visualization item for points.
    """

    def __init__(self, model_item=None, prefix="", parent=None):
        BaseItem.__init__(self, model_item, prefix, parent)

        self._radius = 2
        self._point = None
        self.updatePoint()

    def setRadius(self, radius):
        self._radius = radius
        self.update()

    def radius(self):
        return self._radius

    def __call__(self, model_item=None, parent=None):
        pointitem = PointItem(model_item, parent)
        pointitem.setPen(self.pen())
        pointitem.setBrush(self.brush())
        pointitem.setRadius(self._radius)
        return pointitem

    def dataChange(self):
        self.updatePoint()

    def updateModel(self):
        self._model_item.update({
            self.prefix() + 'x': self.scenePos().x(),
            self.prefix() + 'y': self.scenePos().y(),
        })

    def updatePoint(self):
        if self._model_item is None:
            return

        point = QPointF(float(self._model_item[self.prefix() + 'x']),
                        float(self._model_item[self.prefix() + 'y']))
        if point == self._point:
            return

        self._point = point
        self.prepareGeometryChange()
        self.setPos(self._point)

    def boundingRect(self):
        r = self._radius
        return QRectF(-r, -r, 2 * r, 2 * r)

    def paint(self, painter, option, widget=None):
        BaseItem.paint(self, painter, option, widget)

        pen = self.pen()
        if self.isSelected():
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawEllipse(self.boundingRect())

    def keyPressEvent(self, event):
        step = 1
        if event.modifiers() & Qt.ShiftModifier:
            step = 5
        ds = {Qt.Key_Left:  (-step, 0),
              Qt.Key_Right: (step, 0),
              Qt.Key_Up:    (0, -step),
              Qt.Key_Down:  (0, step)
             }.get(event.key(), None)
        if ds is not None:
            self.moveBy(*ds)
            event.accept()


class RectItem(BaseItem):
    def __init__(self, model_item=None, prefix="", parent=None):
        BaseItem.__init__(self, model_item, prefix, parent)

        self._rect = None
        self._resize = False
        self._resize_start = None
        self._resize_start_rect = None

        self._updateRect(self._dataToRect(self._model_item))
        LOG.debug("Constructed rect %s for model item %s" % (self._rect, model_item))

    def __call__(self, model_item=None, parent=None):
        item = RectItem(model_item, parent)
        item.setPen(self.pen())
        item.setBrush(self.brush())
        return item

    def _dataToRect(self, model_item):
        if model_item is None:
            return QRectF()
        return QRectF(float(model_item[self.prefix() + 'x']),
                      float(model_item[self.prefix() + 'y']),
                      float(model_item[self.prefix() + 'width']),
                      float(model_item[self.prefix() + 'height']))

    def _updateRect(self, rect):
        if rect == self._rect:
            return

        self._rect = rect
        self.prepareGeometryChange()
        self.setPos(rect.topLeft())

    def updateModel(self):
        self._rect = QRectF(self.scenePos(), self._rect.size())
        self._model_item.update({
            self.prefix() + 'x':      float(self._rect.topLeft().x()),
            self.prefix() + 'y':      float(self._rect.topLeft().y()),
            self.prefix() + 'width':  float(self._rect.width()),
            self.prefix() + 'height': float(self._rect.height()),
        })

    def boundingRect(self):
        return QRectF(QPointF(0, 0), self._rect.size())

    def paint(self, painter, option, widget=None):
        BaseItem.paint(self, painter, option, widget)

        pen = self.pen()
        if self.isSelected():
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())

    def dataChange(self):
        rect = self._dataToRect(self._model_item)
        self._updateRect(rect)

    def mousePressEvent(self, event):
        #if event.modifiers() & Qt.ControlModifier != 0:
        if event.button() & Qt.RightButton != 0:
            self._resize = True
            self._resize_start = event.scenePos()
            self._resize_start_rect = QRectF(self._rect)
            event.accept()
        else:
            BaseItem.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self._resize:
            diff = event.scenePos() - self._resize_start
            rect = QRectF(self._resize_start_rect.topLeft(), self._resize_start_rect.bottomRight() + diff).normalized()
            self._updateRect(rect)
            self.updateModel()
            event.accept()
        else:
            BaseItem.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self._resize:
            self._resize = False
            event.accept()
        else:
            BaseItem.mouseReleaseEvent(self, event)

    def keyPressEvent(self, event):
        step = 1
        if event.modifiers() & Qt.ShiftModifier:
            step = 5
        ds = {Qt.Key_Left:  (-step, 0),
              Qt.Key_Right: (step, 0),
              Qt.Key_Up:    (0, -step),
              Qt.Key_Down:  (0, step),
             }.get(event.key(), None)
        if ds is not None:
            if event.modifiers() & Qt.ControlModifier:
                rect = self._rect.adjusted(*((0, 0) + ds))
            else:
                rect = self._rect.adjusted(*(ds + ds))
            self._updateRect(rect)
            self.updateModel()
            event.accept()

class GroupItem(BaseItem):
    items = []

    def __init__(self, model_item=None, prefix="", parent=None):
        self._children = []
        BaseItem.__init__(self, model_item, prefix, parent)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)

        self.createChildren()

    def createChildren(self):
        for callable_, prefix in self.items:
            child = callable_(self._model_item, prefix, self)
            self._children.append(child)

    def setColor(self, *args, **kwargs):
        for c in self._children:
            c.setColor(*args, **kwargs)
        BaseItem.setColor(self, *args, **kwargs)

    def boundingRect(self):
        return self.childrenBoundingRect()

class OccludablePointItem(PointItem):
    def __init__(self, *args, **kwargs):
        PointItem.__init__(self, *args, **kwargs)
        self.updateColor()

    def dataChange(self):
        PointItem.dataChange(self)
        self.updateColor()

    def updateColor(self):
        key = self.prefix() + 'occluded'
        if key in self._model_item:
            occluded = self._model_item[key]
            self.setColor(Qt.red if occluded else Qt.yellow)

    def keyPressEvent(self, event):
        PointItem.keyPressEvent(self, event)
        if event.key() == Qt.Key_O:
            occluded = not self._model_item.get(self.prefix() + 'occluded', False)
            self._model_item[self.prefix() + 'occluded'] = occluded
            self.updateColor()
            event.accept()

class BBoxFaceItem(GroupItem):
    items = [
        (RectItem,            "bbox"),
        (OccludablePointItem, "lec"),
        (OccludablePointItem, "rec"),
        (OccludablePointItem, "mc"),
    ]

class ControlItem(QGraphicsItem):
    def __init__(self, parent=None):
        QGraphicsItem.__init__(self, parent)

        # always have the same size
        self.setFlags(QGraphicsItem.ItemIgnoresTransformations)

    def paint(self, painter, option, widget=None):
        color = QColor('black')
        color.setAlpha(200)
        painter.fillRect(self.boundingRect(), color)

class NPointFacePointItem(QGraphicsEllipseItem):
    def __init__(self, landmark, *args, **kwargs):
        self._landmark = landmark
        QGraphicsEllipseItem.__init__(self, *args, **kwargs)
        self.setFlags(QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemSendsGeometryChanges |
                      QGraphicsItem.ItemSendsScenePositionChanges)

    def landmark(self):
        return self._landmark

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            parent = self.parentItem()
            if parent is not None:
                parent.landmarkChanged(self, value)
        return QAbstractGraphicsShapeItem.itemChange(self, change, value)

    def setColor(self, color):
        self.setPen(color)
        self.update()

class NPointFaceItem(BaseItem):
    landmarks = [
            ("leoc", "left eye outer corner"),
            ("leic", "left eye inner corner"),
            ("reic", "right eye inner corner"),
            ("reoc", "right eye outer corner"),
            ("nt",   "nose tip"),
            ("mlc",  "left mouth corner"),
            ("mrc",  "right mouth corner"),
            ]

    def __init__(self, model_item=None, parent=None):
        self._children = {}
        BaseItem.__init__(self, model_item, parent)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.dataChange()
        self.changeColor()

    def updateModel(self):
        changes = {}
        for lm, lmstr in self.landmarks:
            if lm not in self._children:
                continue
            lmx, lmy = (lm+"x", lm+"y")
            if lmx not in self._model_item or self._model_item[lmx] != self._children[lm].scenePos().x():
                changes[lmx] = self._children[lm].scenePos().x()
            if lmy not in self._model_item or self._model_item[lmy] != self._children[lm].scenePos().y():
                changes[lmy] = self._children[lm].scenePos().y()
        if changes:
            self._model_item.update(changes)

    def dataChange(self):
        for lm, lmstr in self.landmarks:
            lmx, lmy = (lm+"x", lm+"y")
            landmark_present = True
            if lmx not in self._model_item or lmy not in self._model_item:
                landmark_present = False
            elif self._model_item[lmx] < 0 or self._model_item[lmy] < 0:
                landmark_present = False

            if landmark_present:
                px, py = (self._model_item[lmx], self._model_item[lmy])
                if lm in self._children:
                    # Update item position if it is different
                    if px != self._children[lm].scenePos().x() or py != self._children[lm].scenePos().y():
                        self._children[lm].setPos(px, py)
                else:
                    self._children[lm] = NPointFacePointItem(lm, QRectF(-2, -2, 5, 5), self)
                    self._children[lm].setPos(px, py)
            else:
                # Landmark is not present
                if lm in self._children:
                    # Remove landmark from scene
                    pass

    def setColor(self, *args, **kwargs):
        for c in self._children.values():
            c.setColor(*args, **kwargs)
        BaseItem.setColor(self, *args, **kwargs)

    def landmarkChanged(self, item, value):
        self.prepareGeometryChange()
        self.updateModel()

    def boundingRect(self):
        br = self.childrenBoundingRect()
        offset = 0.2 * br.height()
        return br.adjusted(-offset, -offset, +offset, +offset)

    def paint(self, painter, option, widget=None):
        BaseItem.paint(self, painter, option, widget)

        pen = self.pen()
        if self.isSelected():
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())

