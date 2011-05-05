from PyQt4.QtGui import *
from PyQt4.Qt import *
from annotationmodel import DataRole

class ControlItem(QGraphicsItem):
    def __init__(self, parent=None):
        QGraphicsItem.__init__(self, parent)

        # always have the same size
        self.setFlags(QGraphicsItem.ItemIgnoresTransformations)

    def paint(self, painter, option, widget = None):
        color = QColor('black')
        color.setAlpha(200)
        painter.fillRect(self.boundingRect(), color)

class AnnotationGraphicsItem(QAbstractGraphicsShapeItem):
    def __init__(self, index, parent=None):
        QAbstractGraphicsShapeItem.__init__(self, parent)

        self.index_ = index

        self.setFlags(QGraphicsItem.ItemIsSelectable | \
                      QGraphicsItem.ItemIsMovable | \
                      QGraphicsItem.ItemSendsGeometryChanges | \
                      QGraphicsItem.ItemSendsScenePositionChanges)
        self.setPen(QColor('yellow'))

        self.text_font_ = QFont()
        self.text_font_.setPointSize(16)
        self.text_item_ = QGraphicsSimpleTextItem(self)
        self.text_item_.setFont(self.text_font_)
        self.text_item_.setPen(Qt.yellow)
        self.text_item_.setBrush(Qt.yellow)
        self.setText("")

        self._setDelayedDirty(False)

    def _delayedDirty(self):
        return self.delayed_dirty_
    def _setDelayedDirty(self, dirty=True):
        self.delayed_dirty_ = dirty

    def boundingRect(self):
        return QRectF(0, 0, 0, 0)

    def index(self):
        return self.index_

    def setText(self, text, position="upperleft"):
        # TODO use different text items for differenct positions
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
    
    #
    # factory methods for creating the graphics items
    #_________________________________________________________________________________
    _item_types = {}
    
    @staticmethod
    def addItemType(type, constructor, replace=False):
        type = type.lower()
        if type in AnnotationGraphicsItem._item_types and not replace:
            raise Exception("Type %s already has an constructor" % type)

        AnnotationGraphicsItem._item_types[type.lower()] = constructor

    @staticmethod
    def removeItemType(type_str):
        type = type.lower()
        if type in AnnotationGraphicsItem._item_types:
            del AnnotationGraphicsItem._item_types[type]
    
    @staticmethod
    def createItem(index):
        """
        Create an AnnotationGraphicsItem based on the type of the annotation.

        E.g. 
            type == rect  --> AnnotationGraphicsRectItem
            type == point --> AnnotationGraphicsPointItem
        """
        annotation = index.data(DataRole).toPyObject()
        print "createItem:", index.row(), index.column(), annotation

        if annotation is not None and 'type' in annotation:
            type = annotation['type']
            if type in AnnotationGraphicsItem._item_types:
                return AnnotationGraphicsItem._item_types[type](index)

        return None


class AnnotationGraphicsRectItem(AnnotationGraphicsItem):
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

class AnnotationGraphicsPointItem(AnnotationGraphicsItem):
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
               'x': event.pos().x(), 'y': event.pos().y()}
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

class AnnotationGraphicsItemFactory:
    def __init__(self):
        self.items_     = {}
        self.inserters_ = {}

    def register(self, _type, item, inserter, replace=False):
        _type = _type.lower()

        if _type in self.items_ and not replace:
            raise Exception("Type %s already has an item: %s" % \
                             (_type, str(self.items_[_type])))
        else:
            self.items_[_type] = item

        if _type in self.inserters_ and not replace:
            raise Exception("Type %s already has an inserter: %s" % \
                             (_type, str(self.inserters_[_type])))
        else:
            self.inserters_[_type] = inserter

    def clear(self, _type=None):
        if _type is None:
            self.items_     = {}
            self.inserters_ = {}
        else:
            _type = _type.lower()
            if _type in self.items_:
                del self.items_[_type]
            if _type in self.inserters_:
                del self.inserters_[_type]

    def createItem(self, _type, *args, **kwargs):
        _type = _type.lower()

        if _type not in self.items_:
            return None
        return self.items_[_type](*args, **kwargs)

    def createItemInserter(self, _type, *args, **kwargs):
        _type = _type.lower()

        if _type not in self.inserters_:
            return None
        return self.inserters_[_type](*args, **kwargs)

# register common item types
AnnotationGraphicsItem.addItemType('rect',  AnnotationGraphicsRectItem)
AnnotationGraphicsItem.addItemType('point', AnnotationGraphicsPointItem)

