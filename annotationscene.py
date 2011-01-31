from PyQt4.QtGui import *
from PyQt4.QtCore import *
from sceneitems import *
from annotationmodel import ImageRole
import math
import okapy
from okapy.guiqt.utilities import toQImage

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

class AnnotationScene(QGraphicsScene):

    # TODO signal itemadded

    def __init__(self, parent=None):
        super(AnnotationScene, self).__init__(parent)

        self.model_     = None
        self.mode_      = None
        self.inserters_ = {}
        self.inserter_  = None
        self.debug_     = True
        self.message_   = ""
        self.last_key_  = None

        self.setBackgroundBrush(Qt.darkGray)

        self.addItemInserter('point',      PointItemInserter(self))
        self.addItemInserter('rect',       RectItemInserter(self))
        self.addItemInserter('ratiorect',  FixedRatioRectItemInserter(self))
        self.addItemInserter('poly',       PolygonItemInserter(self))
        self.addItemInserter('polygon',    PolygonItemInserter(self))

        self.setMode(None)
        self.reset()

    #
    # getters/setters
    #______________________________________________________________________________________________________
    def model(self):
        return self.model_

    def setModel(self, model):
        if model == self.model_:
            # same model as the current one
            # reset caches anyway, invalidate root
            self.reset()
            return

        # disconnect old signals
        if self.model_ is not None:
            self.disconnect(self.model_, SIGNAL('dataChanged(QModelIndex,QModelIndex)'), self.dataChanged)
            self.disconnect(self.model_, SIGNAL('rowsInserted(QModelIndex,int,int)'), self.rowsInserted)
            self.disconnect(self.model_, SIGNAL('rowsAboutToBeRemoved(QModelIndex,int,int)'), self.rowsAboutToBeRemoved)
            self.disconnect(self.model_, SIGNAL('rowsRemoved(QModelIndex,int,int)'), self.rowsRemoved)
            self.disconnect(self.model_, SIGNAL('modelReset()'), self.reset)
        self.model_ = model

        # connect new signals
        if self.model_ is not None:
            self.connect(self.model_, SIGNAL('dataChanged(QModelIndex,QModelIndex)'), self.dataChanged)
            self.connect(self.model_, SIGNAL('rowsInserted(QModelIndex,int,int)'), self.rowsInserted)
            self.connect(self.model_, SIGNAL('rowsAboutToBeRemoved(QModelIndex,int,int)'), self.rowsAboutToBeRemoved)
            self.connect(self.model_, SIGNAL('rowsRemoved(QModelIndex,int,int)'), self.rowsRemoved)
            self.connect(self.model_, SIGNAL('modelReset()'), self.reset)

        # reset caches, invalidate root
        self.reset()

    def root(self):
        return self.root_

    def setRoot(self, root):
        """
        Set the index of the model which denotes the current image to be
        displayed by the scene.  This can be either the index to a frame in a
        video, or to an image.
        """
        self.root_ = root
        self.clear()
        if not root.isValid():
            return

        assert self.root_.model() == self.model_
        self.image_ = self.root_.data(ImageRole).toPyObject()
        self.pixmap_ = QPixmap(okapy.guiqt.toQImage(self.image_))
        item = QGraphicsPixmapItem(self.pixmap_)
        item.setZValue(-1)
        self.setSceneRect(0, 0, self.pixmap_.width(), self.pixmap_.height())
        self.addItem(item)

        num_items = self.model_.rowCount(self.root_)
        self.insertItems(0, num_items)
        self.update()

    def insertItems(self, first, last):
        assert self.model_ is not None
        assert self.root_.isValid()
        print "insertItems"

        for row in range(first, last+1):
            child = self.root_.child(row, 0)
            item = AnnotationGraphicsItem.createItem(child)
            if item is not None:
                #checked = (child.data(Qt.CheckStateRole).toInt()[0] == Qt.Checked)
                #item.setVisible(checked)
                self.addItem(item)

    def mode(self):
        return self.mode_

    def setMode(self, mode):
        print "setMode :", mode
        self.mode_ = mode

        if self.mode_ == None:
            self.inserter_ = None
            return

        if not self.mode_['type'] in self.inserters_:
            raise InvalidArgumentException("Invalid mode")

        self.inserter_ = self.inserters_[self.mode_['type']]
        self.inserter_.setMode(self.mode_)

    #
    # common methods
    #______________________________________________________________________________________________________
    def reset(self):
        self.clear()
        self.setRoot(QModelIndex())
        self.clearMessage()

    def addItem(self, item):
        QGraphicsScene.addItem(self, item)
        # TODO emit signal itemAdded

    def addItemInserter(self, type, inserter, replace=False):
        type = type.lower()
        if type in self.inserters_ and not replace:
            raise Exception("Type %s already has an inserter" % type)

        self.inserters_[type] = inserter

    def removeItemInserter(self, type):
        type = type.lower()
        if type in self.inserters_:
            del self.inserters_[type]

    #
    # mouse event handlers
    #______________________________________________________________________________________________________
    def mousePressEvent(self, event):
        if self.debug_:
            print "mousePressEvent", self.sceneRect().contains(event.scenePos()), event.scenePos()
        if not self.sceneRect().contains(event.scenePos()):
            # ignore events outside the scene rect
            return
        elif self.inserter_ is not None:
            # insert mode
            self.inserter_.mousePressEvent(event, self.root_)
        else:
            # selection mode
            QGraphicsScene.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.debug_:
            print "mouseReleaseEvent", self.sceneRect().contains(event.scenePos()), event.scenePos()
        if self.inserter_ is not None:
            # insert mode
            self.inserter_.mouseReleaseEvent(event, self.root_)
        else:
            # selection mode
            QGraphicsScene.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        #if self.debug_:
        #   print "mouseMoveEvent", self.sceneRect().contains(event.scenePos()), event.scenePos()
        if self.inserter_ is not None:
            # insert mode
            self.inserter_.mouseMoveEvent(event, self.root_)
        else:
            # selection mode
            QGraphicsScene.mouseMoveEvent(self, event)

    #
    # key event handlers
    #______________________________________________________________________________________________________
    def keyPressEvent(self, event):
        if self.debug_:
           print "keyPressEvent", event

        if self.model_ is None or not self.root_.isValid():
            event.ignore()
            return

        if self.inserter_ is not None:
            # insert mode
            self.inserter_.keyPressEvent(event, self.root_)
        else:
            # selection mode
            if event.key() == Qt.Key_Delete:
                for item in self.selectedItems():
                    index = item.index()
                    index.model().removeAnnotation(index)
                event.accept()
                return

            if ord('0') <= event.key() <= ord('9'):
                if self.last_key_ is None:
                    self.last_key_ = event.key()
                else:
                    id = chr(self.last_key_) + chr(event.key())
                    print "id=", id
                    for item in self.selectedItems():
                        index = item.index()
                        data = dict(index.data(DataRole).toPyObject().iteritems())
                        if data['type'] == 'rect':
                            data['id'] = id
                        index.model().setData(index, QVariant(data), DataRole)
                    self.last_key_ = None

        event.ignore()

    #
    # slots for signals from the model
    # this is the implemenation of the scene as a view of the model
    #______________________________________________________________________________________________________
    def dataChanged(self, indexFrom, indexTo):
        if self.root_ != indexFrom.parent() or self.root_ != indexTo.parent():
            return

        for row in range(indexFrom.row(), indexTo.row()+1):
            item = self.itemFromIndex(indexFrom.sibling(row, 0))
            if item is not None:
                item.dataChanged()

    def rowsInserted(self, index, first, last):
        if self.root_ != index:
            return

        self.insertItems(first, last)


    def rowsAboutToBeRemoved(self, index, first, last):
        if self.root_ != index:
            return

        for row in range(first, last+1):
            item = self.itemFromIndex(index.child(row, 0))
            if item is not None:
                self.removeItem(item)

    def rowsRemoved(self, index, first, last):
        pass

    def itemFromIndex(self, index):
        index = index.model().mapToSource(index)  # TODO: solve this somehow else
        for item in self.items():
            # some graphics items will not have an index method,
            # we just skip these
            if hasattr(item, 'index') and item.index() == index:
                return item
        return None

    #
    # message handling and displaying
    #______________________________________________________________________________________________________
    def setMessage(self, message):
        if self.message_ is not None:
            self.clearMessage()

        if message is None or message == "":
            return

        # TODO don't use text item at all, just draw the text in drawForeground
        self.message_ = message
        self.message_text_item_ = QGraphicsSimpleTextItem(message)
        self.message_text_item_.setPos(20, 20)
        self.invalidate(QRectF(), QGraphicsScene.ForegroundLayer)

    def clearMessage(self):
        if self.message_ is not None:
            self.message_text_item_ = None
            self.message_ = None
            self.invalidate(QRectF(), QGraphicsScene.ForegroundLayer)

    def drawForeground(self, painter, rect):
        QGraphicsScene.drawForeground(self, painter, rect)

        if self.message_ is not None:
            assert self.message_text_item_ is not None

            painter.setTransform(QTransform())
            painter.setBrush(QColor('lightGray'))
            painter.setPen(QPen(QBrush(QColor('black')), 2))

            br = self.message_text_item_.boundingRect()

            painter.drawRoundedRect(QRectF(10, 10, br.width()+20, br.height()+20), 10.0, 10.0)
            painter.setTransform(QTransform.fromTranslate(20, 20))
            painter.setPen(QPen(QColor('black'), 1))

            self.message_text_item_.paint(painter, QStyleOptionGraphicsItem(), None)

