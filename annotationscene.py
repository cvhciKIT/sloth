from PyQt4.QtGui import *
from PyQt4.QtCore import *
from sceneitems import *
from annotationmodel import ImageRole
import math
import okapy
from okapy.guiqt.utilities import toQImage

class ItemInserter:
    #TODO remove model member
    def __init__(self, scene, model=None):
        self.scene_ = scene
        self.model_ = model
        self.mode_  = None

    def setModel(self, model):
        self.model_ = model
    def model(self):
        return self.model_

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

class PointItemInserter(ItemInserter):
    def mousePressEvent(self, event, index):
        pos = event.scenePos()
        # TODO create it in the model instead
        item = QGraphicsEllipseItem(QRectF(pos.x()-1, pos.y()-1, 2, 2))
        self.scene().addItem(item)

        event.accept()

class RectItemInserter(ItemInserter):
    def __init__(self, scene, model=None):
        ItemInserter.__init__(self, scene, model)
        self.current_item_ = None
        self.init_pos_ = None

    def mousePressEvent(self, event, index):
        pos = event.scenePos()
        item = QGraphicsRectItem(QRectF(pos.x(), pos.y(), 0, 0))
        self.current_item_ = item
        self.init_pos_     = pos
        self.scene().addItem(item)
        event.accept()

    def mouseMoveEvent(self, event, index):
        if self.current_item_ is not None:
            assert self.init_pos_ is not None
            pos = event.scenePos()
            rect = QRectF(self.init_pos_.x(), self.init_pos_.y(),
                          pos.x() - self.init_pos_.x(), pos.y() - self.init_pos_.y())
            self.current_item_.setRect(rect.normalized())

        event.accept()

    def mouseReleaseEvent(self, event, index):
        if self.current_item_ is not None:
            if self.current_item_.rect().width() > 1 and \
               self.current_item_.rect().height() > 1:
                # TODO commit to the model
                print "added rect:", self.current_item_
                rect = self.current_item_.rect()
                ann = {'type': 'rect',
                       'x': rect.x(), 'y': rect.y(),
                       'width': rect.width(), 'height': rect.height()}
                index.model().addAnnotation(index, ann)
            self.scene().removeItem(self.current_item_)
            self.current_item_ = None
            self.init_pos_ = None

        event.accept()

class PolygonItemInserter(ItemInserter):
    def __init__(self, scene, model=None):
        ItemInserter.__init__(self, scene, model)
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

        self.setBackgroundBrush(Qt.darkGray)

        self.addItemInserter('point', PointItemInserter(self))
        self.addItemInserter('rect',  RectItemInserter(self))
        self.addItemInserter('poly',  PolygonItemInserter(self))
        self.addItemInserter('polygon',  PolygonItemInserter(self))

        #self.setMode({'type': 'point'})
        self.setMode({'type': 'rect'})
        #self.setMode({'type': 'poly'})

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

    def insertItems(self, first, last):
        assert self.model_ is not None
        assert self.root_.isValid()

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
    # mouse event handler
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
        if self.debug_:
           print "mouseMoveEvent", self.sceneRect().contains(event.scenePos()), event.scenePos()
        if self.inserter_ is not None:
            # insert mode
            self.inserter_.mouseMoveEvent(event, self.root_)
        else:
            # selection mode
            QGraphicsScene.mouseMoveEvent(self, event)

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

