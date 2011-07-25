"""Dies ist das AnnotationScene module"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from sloth.items import *
from sloth.core.exceptions import InvalidArgumentException
from sloth.annotations.model import AnnotationModelItem
from sloth.utils import toQImage
import logging
LOG = logging.getLogger(__name__)

class AnnotationScene(QGraphicsScene):
    mousePositionChanged = pyqtSignal(float, float)
    def __init__(self, labeltool, items=None, inserters=None, parent=None):
        super(AnnotationScene, self).__init__(parent)

        self._model      = None
        self._image_item = None
        self._inserter   = None
        self._scene_item = None
        self._message    = ""
        self._labeltool  = labeltool

        self._itemfactory     = Factory(items)
        self._inserterfactory = Factory(inserters)

        self.setBackgroundBrush(Qt.darkGray)
        self.reset()

    #
    # getters/setters
    #______________________________________________________________________________________________________
    def setModel(self, model):
        if model == self._model:
            # same model as the current one
            # reset caches anyway, invalidate root
            self.reset()
            return

        # disconnect old signals
        if self._model is not None:
            self.disconnect(self._model, SIGNAL('dataChanged(QModelIndex,QModelIndex)'), self.dataChanged)
            self.disconnect(self._model, SIGNAL('rowsInserted(QModelIndex,int,int)'), self.rowsInserted)
            self.disconnect(self._model, SIGNAL('rowsAboutToBeRemoved(QModelIndex,int,int)'), self.rowsAboutToBeRemoved)
            self.disconnect(self._model, SIGNAL('rowsRemoved(QModelIndex,int,int)'), self.rowsRemoved)
            self.disconnect(self._model, SIGNAL('modelReset()'), self.reset)

        self._model = model

        # connect new signals
        if self._model is not None:
            self.connect(self._model, SIGNAL('dataChanged(QModelIndex,QModelIndex)'), self.dataChanged)
            self.connect(self._model, SIGNAL('rowsInserted(QModelIndex,int,int)'), self.rowsInserted)
            self.connect(self._model, SIGNAL('rowsAboutToBeRemoved(QModelIndex,int,int)'), self.rowsAboutToBeRemoved)
            self.connect(self._model, SIGNAL('rowsRemoved(QModelIndex,int,int)'), self.rowsRemoved)
            self.connect(self._model, SIGNAL('modelReset()'), self.reset)

        # reset caches, invalidate root
        self.reset()

    def sceneItem(self):
        return self._scene_item

    def setCurrentImage(self, current_image):
        """
        Set the index of the model which denotes the current image to be
        displayed by the scene.  This can be either the index to a frame in a
        video, or to an image.
        """
        if current_image == self._image_item:
            return
        elif current_image is None:
            self.clear()
            self._image_item = None
            self._image      = None
            self._pixmap     = None
        else:
            self.clear()
            self._image_item = current_image
            assert self._image_item.model() == self._model
            self._image      = self._labeltool.getImage(self._image_item)
            self._pixmap     = QPixmap(toQImage(self._image))
            self._scene_item = QGraphicsPixmapItem(self._pixmap)
            self._scene_item.setZValue(-1)
            self.setSceneRect(0, 0, self._pixmap.width(), self._pixmap.height())
            self.addItem(self._scene_item)

            self.insertItems(0, len(self._image_item.children())-1)
            self.update()

    def insertItems(self, first, last):
        if self._image_item is None:
            return

        assert self._model is not None

        # create a graphics item for each model index
        for row in range(first, last+1):
            child = self._image_item.childAt(row)
            if not isinstance(child, AnnotationModelItem):
                continue
            label_class = child['class']
            item = self._itemfactory.create(label_class, child)
            if item is not None:
                self.addItem(item)
            else:
                LOG.warn("Could not find item for annotation with class '%s'" % label_class)

    def onInserterFinished(self):
        self.sender().inserterFinished.disconnect(self.onInserterFinished)
        self._labeltool.exitInsertMode()
        self._inserter = None

    def onInsertionModeStarted(self, label_class):
        # Abort current inserter
        if self._inserter is not None:
            self._inserter.abort()

        self.deselectAllItems()

        # Add new inserter
        default_properties = self._labeltool.propertyeditor().currentEditorProperties()
        inserter = self._inserterfactory.create(label_class, self._labeltool, self, default_properties)
        if inserter is None:
            raise InvalidArgumentException("Could not find inserter for class '%s' with default properties '%s'" % (label_class, default_properties))
        inserter.inserterFinished.connect(self.onInserterFinished)
        self._inserter = inserter
        LOG.debug("Created inserter for class '%s' with default properties '%s'" % (label_class, default_properties))

    def onInsertionModeEnded(self):
        if self._inserter is not None:
            self._inserter.abort()

    #
    # common methods
    #______________________________________________________________________________________________________
    def reset(self):
        self.clear()
        self.setCurrentImage(None)
        self.clearMessage()

    def clear(self):
        QGraphicsScene.clear(self)
        self._scene_item = None

    def addItem(self, item):
        QGraphicsScene.addItem(self, item)
        # TODO emit signal itemAdded

    #
    # mouse event handlers
    #______________________________________________________________________________________________________
    def mousePressEvent(self, event):
        LOG.debug("mousePressEvent %s %s" % (self.sceneRect().contains(event.scenePos()), event.scenePos()))
        if self._inserter is not None:
            if not self.sceneRect().contains(event.scenePos()) and \
               not self._inserter.allowOutOfSceneEvents():
                # ignore events outside the scene rect
                return
            # insert mode
            self._inserter.mousePressEvent(event, self._image_item)
        else:
            # selection mode
            QGraphicsScene.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        LOG.debug("mouseReleaseEvent %s %s" % (self.sceneRect().contains(event.scenePos()), event.scenePos()))
        if self._inserter is not None:
            # insert mode
            self._inserter.mouseReleaseEvent(event, self._image_item)
        else:
            # selection mode
            QGraphicsScene.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        sp = event.scenePos()
        self.mousePositionChanged.emit(sp.x(), sp.y())
        #LOG.debug("mouseMoveEvent %s %s" % (self.sceneRect().contains(event.scenePos()), event.scenePos()))
        if self._inserter is not None:
            # insert mode
            self._inserter.mouseMoveEvent(event, self._image_item)
        else:
            # selection mode
            QGraphicsScene.mouseMoveEvent(self, event)

    def deselectAllItems(self):
        for item in self.items():
            item.setSelected(False)

    def onSelectionChanged(self):
        model_items = [item.modelItem() for item in self.selectedItems()]
        self._labeltool.treeview().setSelectedItems(model_items)
        self.editSelectedItems()

    def onSelectionChangedInTreeView(self, items):
        block = self.blockSignals(True)
        items = [self.itemFromIndex(item.index()) for item in items]
        for item in self.items():
            item.setSelected(False)
        for item in items:
            if item is not None:
                item.setSelected(True)
        self.blockSignals(block)
        self.editSelectedItems()

    def editSelectedItems(self):
        scene_items = self.selectedItems()
        if self._inserter is None or len(scene_items) > 0:
            items = [item.modelItem() for item in scene_items]
            self._labeltool.propertyeditor().startEditMode(items)

    #
    # key event handlers
    #______________________________________________________________________________________________________
    def selectNextItem(self, reverse=False):
        # disable inserting
        # TODO: forward this to the ButtonArea
        self._inserter = None

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
        LOG.debug("keyPressEvent %s" % event)

        if self._model is None or self._image_item is None:
            event.ignore()
            return

        if self._inserter is not None:
            # insert mode
            self._inserter.keyPressEvent(event, self._image_item)
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
        if self._image_item is None or self._image_item.index() != indexFrom.parent().parent():
            return

        item = self.itemFromIndex(indexFrom.parent())
        if item is not None:
            item.dataChanged()

    def rowsInserted(self, index, first, last):
        if self._image_item is None or self._image_item.index() != index:
            return

        self.insertItems(first, last)

    def rowsAboutToBeRemoved(self, index, first, last):
        if self._image_item is None or self._image_item.index() != index:
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
        if self._message is not None:
            self.clearMessage()

        if message is None or message == "":
            return

        # TODO don't use text item at all, just draw the text in drawForeground
        self._message = message
        self._message_text_item = QGraphicsSimpleTextItem(message)
        self._message_text_item.setPos(20, 20)
        self.invalidate(QRectF(), QGraphicsScene.ForegroundLayer)

    def clearMessage(self):
        if self._message is not None:
            self._message_text_item = None
            self._message = None
            self.invalidate(QRectF(), QGraphicsScene.ForegroundLayer)

    def drawForeground(self, painter, rect):
        QGraphicsScene.drawForeground(self, painter, rect)

        if self._message is not None:
            assert self._message_text_item is not None

            painter.setTransform(QTransform())
            painter.setBrush(QColor('lightGray'))
            painter.setPen(QPen(QBrush(QColor('black')), 2))

            br = self._message_text_item.boundingRect()

            painter.drawRoundedRect(QRectF(10, 10, br.width()+20, br.height()+20), 10.0, 10.0)
            painter.setTransform(QTransform.fromTranslate(20, 20))
            painter.setPen(QPen(QColor('black'), 1))

            self._message_text_item.paint(painter, QStyleOptionGraphicsItem(), None)

