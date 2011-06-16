from PyQt4.QtGui import *
from PyQt4.Qt import *
from sloth.annotations.model import DataRole


class BaseItem(QAbstractGraphicsShapeItem):
    """
    Base class for visualization items.
    """

    def __init__(self, model_item=None, parent=None):
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
        self.setColor(Qt.yellow)

        self._model_item = model_item

        # initialize members
        self.text_ = ""
        self.text_bg_brush_ = None
        self.auto_text_keys_ = []

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

    def setText(self, text=""):
        """
        Sets a text to be displayed on this item.
        """
        self.text_ = text

    def text(self):
        return self.text_

    def setTextBackgroundBrush(self, brush=None):
        """
        Sets the brush to be used to fill the background region
        behind the text. Set to None to not draw a background
        (leave transparent).
        """
        self.text_bg_brush_ = brush

    def textBackgroundBrush(self):
        """
        Returns the background brush for the text region.
        """
        return self.text_bg_brush_

    def setAutoTextKeys(self, keys=[]):
        """
        Sets the keys for which the values from the annotations
        are displayed automatically as text.
        """
        self.auto_text_keys_ = keys

    def autoTextKeys(self):
        """
        Returns the list of keys for which the values from
        the annotations are displayed as text automatically.
        """
        return self.auto_text_keys_

    def _compile_text(self):
        text_lines = []
        if self.text_ != "" and self.text_ is not None:
            text_lines.append(self.text_)
        for key in self.auto_text_keys_:
            text_lines.append("%s: %s" % \
                    (key, self.annotation().get(key, "")))
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
        if self.text_bg_brush_ is not None:
            bg_rect = rect.adjusted(-3, -3, 3, 3)
            painter.fillRect(bg_rect, self.text_bg_brush_)

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

    def __init__(self, model_item=None, parent=None):
        BaseItem.__init__(self, model_item, parent)

        self.radius_ = 2
        self.point_ = None
        self.updatePoint()

    def setRadius(self, radius):
        self.radius_ = radius
        self.update()

    def radius(self):
        return self.radius_

    def __call__(self, model_item=None, parent=None):
        pointitem = PointItem(model_item, parent)
        pointitem.setPen(self.pen())
        pointitem.setBrush(self.brush())
        pointitem.setRadius(self.radius_)
        return pointitem

    def dataChange(self):
        self.updatePoint()

    def updateModel(self):
        self._model_item['x'] = self.scenePos().x()
        self._model_item['y'] = self.scenePos().y()

    def updatePoint(self):
        if self._model_item is None:
            return

        point = QPointF(float(self._model_item['x']),
                        float(self._model_item['y']))
        if point == self.point_:
            return

        self.point_ = point
        self.prepareGeometryChange()
        self.setPos(self.point_)

    def boundingRect(self):
        r = self.radius_
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
    def __init__(self, model_item=None, parent=None):
        BaseItem.__init__(self, model_item, parent)

        self.rect_ = None
        self._updateRect(self._dataToRect(self._model_item))

    def __call__(self, model_item=None, parent=None):
        item = RectItem(model_item, parent)
        item.setPen(self.pen())
        item.setBrush(self.brush())
        return item

    def _dataToRect(self, model_item):
        if model_item is None:
            return QRectF()
        if model_item.has_key('w'):
            w = model_item['w']
        if model_item.has_key('width'):
            w = model_item['width']
        if model_item.has_key('h'):
            h = model_item['h']
        if model_item.has_key('height'):
            h = model_item['height']
        return QRectF(float(model_item['x']), float(model_item['y']),
                      float(w), float (h))

    def _updateRect(self, rect):
        if not rect.isValid():
            return
        if rect == self.rect_:
            return

        self.rect_ = rect
        self.prepareGeometryChange()
        self.setPos(rect.topLeft())

    def updateModel(self):
        self.rect_ = QRectF(self.scenePos(), self.rect_.size())
        self._model_item['x'] = self.rect_.topLeft().x()
        self._model_item['y'] = self.rect_.topLeft().y()
        if self._model_item.has_key('width'):
            self._model_item['width'] = float(self.rect_.width())
        if self._model_item.has_key('w'):
            self._model_item['w'] = float(self.rect_.width())
        if self._model_item.has_key('height'):
            self._model_item['height'] = float(self.rect_.height())
        if self._model_item.has_key('h'):
            self._model_item['h'] = float(self.rect_.height())

    def boundingRect(self):
        return QRectF(QPointF(0, 0), self.rect_.size())

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
                rect = self.rect_.adjusted(*((0, 0) + ds))
            else:
                rect = self.rect_.adjusted(*(ds + ds))
            self._updateRect(rect)
            # Need self.updateModel() ?
            event.accept()


class ControlItem(QGraphicsItem):
    def __init__(self, parent=None):
        QGraphicsItem.__init__(self, parent)

        # always have the same size
        self.setFlags(QGraphicsItem.ItemIgnoresTransformations)

    def paint(self, painter, option, widget=None):
        color = QColor('black')
        color.setAlpha(200)
        painter.fillRect(self.boundingRect(), color)
