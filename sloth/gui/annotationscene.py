"""Dies ist das AnnotationScene module"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from sloth.items import *
from sloth.annotations.model import TypeRole
from sloth.core.exceptions import InvalidArgumentException
import okapy

class AnnotationScene(QGraphicsScene):
    """Dies ist ein Test"""

    # TODO signal itemadded

    def __init__(self, labeltool, items=None, inserters=None, parent=None):
        super(AnnotationScene, self).__init__(parent)

        self.model_     = None
        self.mode_      = None
        self.inserter_  = None
        self.debug_     = True
        self.message_   = ""
        self.last_key_  = None
        self.labeltool_ = labeltool

        self.itemfactory_     = Factory(items)
        self.inserterfactory_ = Factory(inserters)

        self.setBackgroundBrush(Qt.darkGray)

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
        self.image_item_ = None
        self.image_      = None
        self.pixmap_     = None

        self.root_ = root
        self.clear()
        if not root.isValid():
            return

        assert self.root_.model() == self.model_
        self.image_item_ = self.model_.itemFromIndex(root)
        self.image_      = self.labeltool_.getImage(self.image_item_)
        self.pixmap_     = QPixmap(okapy.guiqt.toQImage(self.image_))
        item             = QGraphicsPixmapItem(self.pixmap_)
        item.setZValue(-1)
        self.setSceneRect(0, 0, self.pixmap_.width(), self.pixmap_.height())
        self.addItem(item)

        num_items = self.model_.rowCount(self.root_)
        self.insertItems(0, num_items)
        self.update()

    def insertItems(self, first, last):
        if not self.root_.isValid():
            return

        assert self.model_ is not None

        # create a graphics item for each model index
        for row in range(first, last+1):
            child = self.root_.child(row, 0) # get index
            _type = str(child.data(TypeRole).toPyObject()) # get type from index
            item = self.itemfactory_.create(_type, self.model_.itemFromIndex(child))    # create graphics item from factory
            if item is not None:
                self.addItem(item)

    def onInserterFinished(self):
        self.sender().inserterFinished.disconnect(self.onInserterFinished)
        self.inserter_ = None

    def setMode(self, mode):
        print "setMode :", mode

        # Abort current inserter
        if self.inserter_ is not None:
            self.inserter_.abort()

        # Add new inserter
        if mode is not None:
            inserter = self.inserterfactory_.create(mode['type'], self.labeltool_, self, mode)
            if inserter is None:
                raise InvalidArgumentException("Invalid mode")
            inserter.inserterFinished.connect(self.onInserterFinished)
            self.inserter_ = inserter

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

    #
    # mouse event handlers
    #______________________________________________________________________________________________________
    def mousePressEvent(self, event):
        if self.debug_:
            print "mousePressEvent", self.sceneRect().contains(event.scenePos()), event.scenePos()
        if self.inserter_ is not None:
            if not self.sceneRect().contains(event.scenePos()) and \
               not self.inserter_.allowOutOfSceneEvents():
                # ignore events outside the scene rect
                return
            # insert mode
            self.inserter_.mousePressEvent(event, self.image_item_)
        else:
            # selection mode
            QGraphicsScene.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.debug_:
            print "mouseReleaseEvent", self.sceneRect().contains(event.scenePos()), event.scenePos()
        if self.inserter_ is not None:
            # insert mode
            self.inserter_.mouseReleaseEvent(event, self.image_item_)
        else:
            # selection mode
            QGraphicsScene.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        #if self.debug_:
        #   print "mouseMoveEvent", self.sceneRect().contains(event.scenePos()), event.scenePos()
        if self.inserter_ is not None:
            # insert mode
            self.inserter_.mouseMoveEvent(event, self.image_item_)
        else:
            # selection mode
            QGraphicsScene.mouseMoveEvent(self, event)


    def onSelectionChanged(self):
        model_items = [item.modelItem() for item in self.selectedItems()]
        self.labeltool_.treeview().setSelectedItems(model_items)

    def onSelectionChangedInTreeView(self, items):
        block = self.blockSignals(True)
        items = [self.itemFromIndex(item.index()) for item in items]
        for item in self.items():
            item.setSelected(False)
        for item in items:
            if item is not None:
                item.setSelected(True)
        self.blockSignals(block)

    #
    # key event handlers
    #______________________________________________________________________________________________________
    def selectNextItem(self, reverse=False):
        # disable inserting
        # TODO: forward this to the ButtonArea
        self.inserter_ = None

        # set focus to the view, so that subsequent keyboard events are forwarded to the scene
        if len(self.views()) > 0:
            self.views()[0].setFocus(True)

        # get the current selected item if there is any
        selected_item = None
        found = True
        if len(self.selectedItems()) > 0:
            selected_item = self.selectedItems()[0]
            selected_item.setSelected(False)
            found = False

        items = [item for item in self.items()
                      if item.flags() & QGraphicsItem.ItemIsSelectable] * 2
        if reverse:
            items.reverse()

        for item in items:
            if item is selected_item:
                found = True
                continue

            if found and item is not selected_item:
                item.setSelected(True)
                break

    def keyPressEvent(self, event):
        if self.debug_:
           print "keyPressEvent", event

        if self.model_ is None or not self.root_.isValid():
            event.ignore()
            return

        if self.inserter_ is not None:
            # insert mode
            self.inserter_.keyPressEvent(event, self.image_item_)
        else:
            # selection mode
            if event.key() == Qt.Key_Delete:
                for item in self.selectedItems():
                    item.modelItem().delete()
                event.accept()

            elif event.key() == Qt.Key_Escape:
                # deselect all selected items
                for item in self.selectedItems():
                    item.setSelected(False)

            elif len(self.selectedItems()) > 0:
                for item in self.selectedItems():
                    item.keyPressEvent(event)

        QGraphicsScene.keyPressEvent(self, event)
        #event.ignore()

    #
    # slots for signals from the model
    # this is the implemenation of the scene as a view of the model
    #______________________________________________________________________________________________________
    def dataChanged(self, indexFrom, indexTo):
        if not self.root_.isValid():
            return

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

