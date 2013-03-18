from PyQt4.QtGui import *
from PyQt4.Qt import *

import logging
LOG = logging.getLogger(__name__)

# convenience functions for creating hotkey functions
class cycleValue:
    def __init__(self, itemkey, valuelist):
        self.itemkey = itemkey
        self.valuelist = valuelist

    def __call__(self, item):
        if isinstance(self.itemkey, IgnorePrefix):
            key = self.itemkey.value
        else:
            key = item.prefix() + self.itemkey

        if len(self.valuelist) > 0:
            oldvalue = item._model_item.get(key, None)
            if oldvalue is None:
                nextindex = 0
            else:
                try:
                    nextindex = self.valuelist.index(oldvalue) + 1
                    nextindex %= len(self.valuelist)
                except ValueError:
                    nextindex = 0
            newvalue = self.valuelist[nextindex]
            if newvalue is None:
                if oldvalue is not None:
                    item._model_item.delete(key)
            else:
                item._model_item[key] = self.valuelist[nextindex]
            item.dataChanged()

def setValue(itemkey, newvalue):
    return lambda self: _setValue(self, itemkey, newvalue)

def _setValue(self, itemkey, newvalue):
    if isinstance(itemkey, IgnorePrefix):
        itemkey = itemkey.value
    else:
        itemkey = self.prefix() + itemkey
    oldvalue = self._model_item.get(itemkey, None)
    if newvalue is None:
        if oldvalue is not None:
            self._model_item.delete(itemkey)
    elif newvalue != oldvalue:
        self._model_item[itemkey] = newvalue
    self.dataChanged()


class IgnorePrefix:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

class BaseItem(QAbstractGraphicsShapeItem):
    """
    Base class for visualization items.
    """

    cycleValuesOnKeypress = {}
    hotkeys = {}
    defaultAutoTextKeys = []

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
        self.setFlags(QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemSendsGeometryChanges |
                      QGraphicsItem.ItemSendsScenePositionChanges)

        self._model_item = model_item
        if self._model_item is not None:
            self._model_item.model().dataChanged.connect(self.onDataChanged)

        # initialize members
        self._prefix = prefix
        self._auto_text_keys = self.defaultAutoTextKeys[:]
        self._text = ""
        self._text_bg_brush = None
        self._text_item = QGraphicsTextItem(self)
        self._text_item.setPos(0, 0)
        self._text_item.setAcceptHoverEvents(False)
        self._text_item.setFlags(QGraphicsItem.ItemIgnoresTransformations)
        self._text_item.setHtml(self._compile_text())
        self._valid = True

        if len(self.cycleValuesOnKeypress) > 0:
            logging.warning("cycleValueOnKeypress is deprecated and will be removed in the future. Set BaseItem.hotkeys instead with cycleValue()")

        self.changeColor()

    def changeColor(self):
        if self._model_item is not None:
            c = self._model_item.getColor()
            if c is not None:
                self.setColor(c)
                return
        self.setColor(Qt.yellow)

    def onDataChanged(self, indexFrom, indexTo):
        # FIXME why is this not updated, when changed graphically via attribute box ?
        #print "onDataChanged", self._model_item.index(), indexFrom, indexTo, indexFrom.parent()
        if indexFrom == self._model_item.index():
            self.changeColor()
            #print "hit"
            # self._text_item.setHtml(self._compile_text())

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

    def setPen(self, pen):
        QAbstractGraphicsShapeItem.setPen(self, pen)
        self._text_item.setDefaultTextColor(pen)

    def setText(self, text=""):
        """
        Sets a text to be displayed on this item.
        """
        self._text = text
        self._text_item.setHtml(self._compile_text())

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
        self._text_item.setHtml(self._compile_text())

    def autoTextKeys(self):
        """
        Returns the list of keys for which the values from
        the annotations are displayed as text automatically.
        """
        return self._auto_text_keys

    def isValid(self):
        """
        Return whether this graphics item is valid, i.e. has
        a matching, valid model item connected to it.  An item is
        by default valid, will only be set invalid on failure.
        """
        return self._valid

    def setValid(self, val):
        self._valid = val

    def _compile_text(self):
        text_lines = []
        if self._text != "" and self._text is not None:
            text_lines.append(self._text)
        for key in self._auto_text_keys:
            text_lines.append("%s: %s" % \
                    (key, self._model_item.get(key, "")))
        return '<br/>'.join(text_lines)

    def dataChanged(self):
        self.dataChange()
        self._text_item.setHtml(self._compile_text())
        self.update()

    def dataChange(self):
        pass

    def updateModel(self, ann=None):
        if ann is not None:
            self._model_item.update(ann)

    def boundingRect(self):
        return QRectF(0, 0, 0, 0)

    def setColor(self, color):
        self.setPen(color)
        self.setBrush(color)
        self.update()

    def paint(self, painter, option, widget=None):
        pass

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.updateModel()
        return QAbstractGraphicsShapeItem.itemChange(self, change, value)

    def keyPressEvent(self, event):
        """
        This handles the value cycling as defined in cycleValuesOnKeypress.
        """
        if str(event.text()) in self.cycleValuesOnKeypress:
            itemkey, valuelist = self.cycleValuesOnKeypress[str(event.text())]
            if isinstance(itemkey, IgnorePrefix):
                itemkey = itemkey.value
            else:
                itemkey = self.prefix() + itemkey
            if len(valuelist) > 0:
                oldvalue = self._model_item.get(itemkey, None)
                if oldvalue is None:
                    nextindex = 0
                else:
                    try:
                        nextindex = valuelist.index(oldvalue) + 1
                        nextindex %= len(valuelist)
                    except ValueError:
                        nextindex = 0
                newvalue = valuelist[nextindex]
                if newvalue is None:
                    if oldvalue is not None:
                        self._model_item.delete(itemkey)
                else:
                    self._model_item[itemkey] = valuelist[nextindex]
                self.dataChanged()
                event.accept()
        elif str(event.text()) in self.hotkeys:
            self.hotkeys[str(event.text())](self)
            event.accept()


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
        self.prepareGeometryChange()
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

        try:
            point = QPointF(float(self._model_item[self.prefix() + 'x']),
                            float(self._model_item[self.prefix() + 'y']))
        except KeyError as e:
            LOG.error("PointItem: Could not find expected key in item: "
                      + str(e) + ". Check your config!")
            self.setValid(False)
            self._point = None
            return

        if point == self._point:
            return

        self.prepareGeometryChange()
        self._point = point
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
        BaseItem.keyPressEvent(self, event)
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
        self._upper_half_clicked = None
        self._left_half_clicked = None

        self._updateRect(self._dataToRect(self._model_item))
        LOG.debug("Constructed rect %s for model item %s" %
                  (self._rect, model_item))

    def __call__(self, model_item=None, parent=None):
        item = RectItem(model_item, parent)
        item.setPen(self.pen())
        item.setBrush(self.brush())
        return item

    def _dataToRect(self, model_item):
        if model_item is None:
            return QRectF()

        try:
            return QRectF(float(model_item[self.prefix() + 'x']),
                          float(model_item[self.prefix() + 'y']),
                          float(model_item[self.prefix() + 'width']),
                          float(model_item[self.prefix() + 'height']))
        except KeyError as e:
            LOG.error("RectItem: Could not find expected key in item: "
                      + str(e) + ". Check your config!")
            self.setValid(False)
            return QRectF()

    def _updateRect(self, rect):
        if rect == self._rect:
            return

        self.prepareGeometryChange()
        self._rect = rect
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
            self._upper_half_clicked = (event.scenePos().y() < self._resize_start_rect.center().y())
            self._left_half_clicked  = (event.scenePos().x() < self._resize_start_rect.center().x())
            event.accept()
        else:
            BaseItem.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self._resize:
            diff = event.scenePos() - self._resize_start
            if self._left_half_clicked:
                x = self._resize_start_rect.x() + diff.x()
                w = self._resize_start_rect.width() - diff.x()
            else:
                x = self._resize_start_rect.x()
                w = self._resize_start_rect.width() + diff.x()

            if self._upper_half_clicked:
                y = self._resize_start_rect.y() + diff.y()
                h = self._resize_start_rect.height() - diff.y()
            else:
                y = self._resize_start_rect.y()
                h = self._resize_start_rect.height() + diff.y()

            rect = QRectF(QPointF(x,y), QSizeF(w, h)).normalized()

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
        BaseItem.keyPressEvent(self, event)
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


class MultiPointItem(BaseItem):
    def __init__(self, model_item=None, prefix="pointlist", parent=None):
        BaseItem.__init__(self, model_item, prefix, parent)

        # make it non-movable for now
        self.setFlags(QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges |
                      QGraphicsItem.ItemSendsScenePositionChanges)
        self._points = None

        self._updatePoints(self._dataToPoints(self._model_item))
        LOG.debug("Constructed points %s for model item %s" %
                  (self._points, model_item))

    def __call__(self, model_item=None, parent=None):
        item = MultiPointItem(model_item, parent)
        item.setPen(self.pen())
        item.setBrush(self.brush())
        return item

    def _dataToPoints(self, model_item):
        if model_item is None:
            return []

        try:
            return model_item[self.prefix()]
        except KeyError as e:
            LOG.error("MultiPointItem: Could not find expected key in item: "
                      + str(e) + ". Check your config!")
            self.setValid(False)
            return QRectF()

    def _updatePoints(self, points):
        if points == self._points:
            return

        self.prepareGeometryChange()
        self._points = points
        self.setPos(QPointF(0, 0))

    def updateModel(self):
        pass

    def boundingRect(self):
        xmin = min(self._points[::2])
        xmax = max(self._points[::2])
        ymin = min(self._points[1::2])
        ymax = max(self._points[1::2])
        return QRectF(xmin, ymin, xmax - xmin, ymax - ymin)

    def paint(self, painter, option, widget=None):
        BaseItem.paint(self, painter, option, widget)

        pen = self.pen()
        if self.isSelected():
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        for k in range(len(self._points)/2):
            x, y = self._points[2*k:2*k+2]
            painter.drawEllipse(QRectF(x-1, y-1, 2, 2))

    def dataChange(self):
        points = self._dataToPoints(self._model_item)
        self._updateRect(points)


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
        br = QRectF()
        for item in self.childItems():
            if item is self._text_item:
                continue
            br |= item.mapRectToParent(item.boundingRect())
        return br


class OccludablePointItem(PointItem):
    hotkeys = {
        'o': cycleValue('occluded', [True, False])
    }

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


class IDRectItem(RectItem):
    hotkeys = dict(
        [('i',    cycleValue(IgnorePrefix('id'), range(36)))] +
        [(str(i), cycleValue(IgnorePrefix('id'), [i])) for i in range(10)] +
        [(chr(i-10+65).lower(), cycleValue(IgnorePrefix('id'), [i])) for i in range(10, 36)]
    )
    defaultAutoTextKeys = ['id']


class BBoxFaceItem(GroupItem):
    items = [
        (IDRectItem,          "bbox"),
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


class NPointFaceItem(GroupItem):
    items = [
        (OccludablePointItem, "leoc"), # left eye outer center
        (OccludablePointItem, "lec"),  # left eye center
        (OccludablePointItem, "leic"), # left eye inner center
        (OccludablePointItem, "reic"), # right eye inner center
        (OccludablePointItem, "rec"),  # right eye center
        (OccludablePointItem, "reoc"), # right eye outer center
        (OccludablePointItem, "nt"), # nose tip
        (OccludablePointItem, "nl"), # nose left
        (OccludablePointItem, "nr"), # nose right
        (OccludablePointItem, "nc"), # nose center
        (OccludablePointItem, "ulc"), # upper lip center
        (OccludablePointItem, "llc"), # lower lip center
        (OccludablePointItem, "mc"), # mouth center
        (OccludablePointItem, "lmc"), # left mouth corner
        (OccludablePointItem, "rmc"), # right mouth corner
        (OccludablePointItem, "le"), # left ear
        (OccludablePointItem, "re"), # right ear
        (OccludablePointItem, "cc"), # chin center
    ]

    def __init__(self, model_item=None, prefix="", parent=None):
        GroupItem.__init__(self, model_item, prefix, parent)

    def createChildren(self):
        for callable_, prefix in self.items:
            if prefix + 'x' in self._model_item and \
               prefix + 'y' in self._model_item:
                child = callable_(self._model_item, prefix, self)
                self._children.append(child)

    def boundingRect(self):
        br = GroupItem.boundingRect(self)
        offset = 0.2 * br.height()
        return br.adjusted(-offset, -offset, +offset, +offset)

    def paint(self, painter, option, widget=None):
        GroupItem.paint(self, painter, option, widget)

        pen = self.pen()
        if self.isSelected():
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())
