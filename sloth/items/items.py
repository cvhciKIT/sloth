from PyQt4.QtGui import *
from PyQt4.Qt import *
from sloth.annotations.model import DataRole

class ControlItem(QGraphicsItem):
    def __init__(self, parent=None):
        QGraphicsItem.__init__(self, parent)

        # always have the same size
        self.setFlags(QGraphicsItem.ItemIgnoresTransformations)

    def paint(self, painter, option, widget = None):
        color = QColor('black')
        color.setAlpha(200)
        painter.fillRect(self.boundingRect(), color)

class BaseItem(QAbstractGraphicsShapeItem):
    """
    Base class for visualization items.
    """

    def __init__(self, index=None, data=None, parent=None):
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

        # store index and label data
        self.index_ = index
        if data is None and index is not None:
            data = self.index().data(DataRole).toPyObject()
        self.data_ = data

    def annotation(self):
        return self.data_

    def index(self):
        return self.index_

    def updateModel(self, data=None):
        if data is not None:
            self.index().model().setData(self.index(), QVariant(self.data_), DataRole)

    def paint(self, painter, option, widget=None):
        pass

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

    def __init__(self, index=None, data=None, parent=None):
        BaseItem.__init__(self, index, data, parent)

        self.radius_ = 2
        self.point_ = None
        self.updatePoint()

    def setRadius(self, radius):
        self.radius_ = radius
        self.update()

    def radius(self):
        return self.radius_

    def __call__(self, index=None, data=None, parent=None):
        pointitem = PointItem(index, data, parent)
        pointitem.setPen(self.pen())
        pointitem.setBrush(self.brush())
        pointitem.setRadius(self.radius_)
        return pointitem

    def updateModel(self):
        self.data_['x'] = self.scenePos().x()
        self.data_['y'] = self.scenePos().y()
        self.index().model().setData(self.index(), QVariant(self.data_), DataRole)

    def updatePoint(self):
        if self.data_ is None:
            return

        point = QPointF(float(self.data_['x']),
                        float(self.data_['y']))
        if point == self.point_:
            return

        self.point_ = point
        self.prepareGeometryChange()
        self.setPos(self.point_)

    def boundingRect(self):
        r = self.radius_
        return QRectF(-r, -r, 2*r, 2*r)

    def paint(self, painter, option, widget=None):
        pen = self.pen()
        if self.isSelected():
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawEllipse(self.boundingRect())

    def dataChanged(self):
        self.data_ = self.index().data(DataRole).toPyObject()
        self.updatePoint()

    def keyPressEvent(self, event):
        step = 1
        if event.modifiers() & Qt.ShiftModifier:
            step = 5
        ds = { Qt.Key_Left:  (-step, 0),
               Qt.Key_Right: (step, 0),
               Qt.Key_Up:    (0, -step),
               Qt.Key_Down:  (0, step),
             }.get(event.key(), None)
        if ds is not None:
            self.moveBy(*ds)
            event.accept()

class RectItem(BaseItem):
    def __init__(self, index=None, data=None, parent=None):
        BaseItem.__init__(self, index, data, parent)

        self.rect_ = None
        self._updateRect(self._dataToRect(self.data_))
        self._updateText()

    def __call__(self, index=None, data=None, parent=None):
        item = RectItem(index, data, parent)
        item.setPen(self.pen())
        item.setBrush(self.brush())
        return item

    def _dataToRect(self, data):
        if data is None:
            return QRectF()
        return QRectF(float(data['x']), float(data['y']),
                      float(data.get('width',  data.get('w'))),
                      float(data.get('height', data.get('h'))))

    def _updateRect(self, rect):
        if not rect.isValid():
            return
        if rect == self.rect_:
            return

        self.rect_ = rect
        self.prepareGeometryChange()
        self.setPos(rect.topLeft())

    def _updateText(self):
        if self.data_ is None:
            return
        if 'id' in self.data_:
            self.setText("id: " + str(self.data_['id']))

    def updateModel(self):
        self.rect_ = QRectF(self.scenePos(), self.rect_.size())
        self.data_['x'] = self.rect_.topLeft().x()
        self.data_['y'] = self.rect_.topLeft().y()
        if 'width'  in self.data_: self.data_['width']  = float(self.rect_.width())
        if 'w'      in self.data_: self.data_['w']      = float(self.rect_.width())
        if 'height' in self.data_: self.data_['height'] = float(self.rect_.height())
        if 'h'      in self.data_: self.data_['h']      = float(self.rect_.height())

        self.index().model().setData(self.index(), QVariant(self.data_), DataRole)

    def boundingRect(self):
        return QRectF(QPointF(0, 0), self.rect_.size())

    def paint(self, painter, option, widget = None):
        pen = self.pen()
        if self.isSelected():
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())

    def dataChanged(self):
        self.data_ = self.index().data(DataRole).toPyObject()
        rect = self._dataToRect(self.data_)
        self._updateRect(rect)
        self._updateText()

    def keyPressEvent(self, event):
        step = 1
        if event.modifiers() & Qt.ShiftModifier:
            step = 5
        ds = { Qt.Key_Left:  (-step, 0),
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
            event.accept()


class AnnotationGraphicsItem(QAbstractGraphicsShapeItem):
    """
    Old base class for items.  Use BaseItem now!
    """
    def __init__(self, index, parent=None):
        QAbstractGraphicsShapeItem.__init__(self, parent)

        self.index_ = index

        self.setFlags(QGraphicsItem.ItemIsSelectable | \
                      QGraphicsItem.ItemIsMovable | \
                      QGraphicsItem.ItemSendsGeometryChanges | \
                      QGraphicsItem.ItemSendsScenePositionChanges)
        self.setColor(Qt.yellow)

        self.text_font_ = QFont()
        self.text_font_.setPointSize(16)
        self.text_item_ = QGraphicsSimpleTextItem(self)
        self.text_item_.setFont(self.text_font_)
        self.text_item_.setPen(Qt.yellow)
        self.text_item_.setBrush(Qt.yellow)
        self.setText("")

        self._setDelayedDirty(False)

    def setColor(self, color):
        self.setPen(color)
        self.setBrush(color)

    def _delayedDirty(self):
        return self.delayed_dirty_
    def _setDelayedDirty(self, dirty=True):
        self.delayed_dirty_ = dirty

    def boundingRect(self):
        return QRectF(0, 0, 0, 0)

    def index(self):
        return self.index_

    def setText(self, text, position="upperleft"):
        # TODO use different text items for different positions
        self.text_item_.setText(text)
        self.text_item_.setPos(0, 0)
        self.text_item_.update()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            self.setControlsVisible(value.toBool())
        return QGraphicsItem.itemChange(self, change, value)

    def dataChanged(self):
        pass

    def setControlsVisible(self, visible=True):
        self.controls_visible_ = visible
        print "Controls visible:", visible
        #for corner in self.corner_items_:
        #    corner.setVisible(self.controls_enabled_ and self.controls_visible_)

class OldRectItem(AnnotationGraphicsItem):
    def __init__(self, index, parent=None):
        AnnotationGraphicsItem.__init__(self, index, parent)

        self.data_ = self.index().data(DataRole).toPyObject()
        self.rect_ = None
        self._updateRect(self._dataToRect(self.data_))
        self._updateText()

    def _dataToRect(self, data):
        return QRectF(float(data['x']), float(data['y']),
                      float(data.get('width',  data.get('w'))),
                      float(data.get('height', data.get('h'))))

    def _updateRect(self, rect):
        if not rect.isValid():
            return
        if rect == self.rect_:
            return

        self.rect_ = rect
        self.prepareGeometryChange()
        self.setPos(rect.topLeft())
        #self.layoutChildren()
        #self.update()

    def _updateText(self):
        if 'id' in self.data_:
            self.setText("id: " + str(self.data_['id']))

    def updateModel(self):
        if not self._delayedDirty():
            self.rect_ = QRectF(self.scenePos(), self.rect_.size())
            self.data_['x'] = self.rect_.topLeft().x()
            self.data_['y'] = self.rect_.topLeft().y()
            if 'width'  in self.data_: self.data_['width']  = float(self.rect_.width())
            if 'w'      in self.data_: self.data_['w']      = float(self.rect_.width())
            if 'height' in self.data_: self.data_['height'] = float(self.rect_.height())
            if 'h'      in self.data_: self.data_['h']      = float(self.rect_.height())

            print "updateModel", self.data_
            self.index().model().setData(self.index(), QVariant(self.data_), DataRole)

    def boundingRect(self):
        return QRectF(QPointF(0, 0), self.rect_.size())

    def paint(self, painter, option, widget = None):
        pen = self.pen()
        if self.isSelected():
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            self.updateModel()
        return AnnotationGraphicsItem.itemChange(self, change, value)

    def dataChanged(self):
        self.data_ = self.index().data(DataRole).toPyObject()
        rect = self._dataToRect(self.data_)
        self._updateRect(rect)
        self._updateText()

    def keyPressEvent(self, event):
        step = 1
        if event.modifiers() & Qt.ShiftModifier:
            step = 5
        ds = { Qt.Key_Left:  (-step, 0),
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
            event.accept()

class OldPointItem(AnnotationGraphicsItem):
    def __init__(self, index, parent=None):
        AnnotationGraphicsItem.__init__(self, index, parent)

        self.display_size_ = 3

        self.data_ = self.index().data(DataRole).toPyObject()
        self.point_ = None
        self.updatePoint()

    def updatePoint(self):
        point = QPointF(float(self.data_['x']),
                        float(self.data_['y']))
        if point == self.point_:
            return

        self.point_ = point
        self.prepareGeometryChange()
        self.setPos(self.point_)
        #self.layoutChildren()
        #self.update()

    def updateModel(self):
        if not self._delayedDirty():
            self.data_['x'] = self.scenePos().x()
            self.data_['y'] = self.scenePos().y()
            self.index().model().setData(self.index(), QVariant(self.data_), DataRole)

    def boundingRect(self):
        s = self.display_size_
        return QRectF(-s/2, -s/2, s, s)

    def paint(self, painter, option, widget = None):
        pen = self.pen()
        if self.isSelected():
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawEllipse(self.boundingRect())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.updateModel()
        return AnnotationGraphicsItem.itemChange(self, change, value)

    def dataChanged(self):
        self.data_ = self.index().data(DataRole).toPyObject()
        self.updatePoint()

class LineItem(AnnotationGraphicsItem):
    def __init__(self, pos, endPoint, parent=None):
        AnnotationGraphicsItem.__init__(self, False, parent)
        self.setPos(pos)
        self.endPoint_ = endPoint
        self.setFlags(QGraphicsItem.ItemIsSelectable|QGraphicsItem.ItemIsMovable)
        self.setPen(QColor('green'))

    def resizeContents(self, rect):
        pass

    def boundingRect(self):
        width = abs(self.endPoint_.x() - self.pos().x())
        height = abs(self.endPoint_.y() - self.pos().y())
        return QRectF(-10, -10, width, height)

    def paint(self, painter, option, widget = None):
        pen = self.pen()
        if self.isSelected():
            pen.setColor(QColor('red'))
        painter.setPen(pen)
        painter.drawLine(self.pos, self.endPoint_)

    def itemChange(self, change, value):
        return AnnotationGraphicsItem.itemChange(self, change, value)

