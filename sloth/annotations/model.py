"""
The annotationmodel module contains the classes for the AnnotationModel.
"""
from PyQt4.QtGui import QTreeView, QItemSelection, QItemSelectionModel, QSortFilterProxyModel, QAbstractItemView
from PyQt4.QtCore import QModelIndex, QPersistentModelIndex, QAbstractItemModel, QVariant, Qt, pyqtSignal
import os.path
import copy
from collections import MutableMapping

ItemRole, TypeRole, DataRole, ImageRole = [Qt.UserRole + i + 1 for i in range(4)]

class ModelItem(MutableMapping):
    def __init__(self):
        if not hasattr(self, "_children"):
            self._children = []
        if not hasattr(self, "_pindex"):
            self._pindex   = []
        if not hasattr(self, "_model"):
            self._model    = None
        if not hasattr(self, "_parent"):
            self._parent   = None
        if not hasattr(self, "_columns"):
            self._columns  = 1
        if not hasattr(self, "_dict"):
            self._dict     = {}

    # Methods for MutableMapping
    def __len__(self):
        return len(self._dict)

    def __iter__(self):
        return self._dict.iterkeys()

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, value):
        if key not in self._dict or self._dict[key] != value:
            self._dict[key] = value
            self._valueChanged()

    def __delitem__(self, key):
        del self._dict[key]
        self._valueChanged()

    def has_key(self, key):
        return self.__contains__(key)

    def clear(self):
        if len(self) > 0:
            MutableMapping.clear(self)
            self._valueChanged()

    def update(self, other=None, **kwargs):
        MutableMapping.update(self, other, **kwargs)
        # TODO: Only call _valueChanged, if anything actually changed...
        self._valueChanged()

    def _valueChanged(self):
        pass

    def children(self):
        return self._children

    def model(self):
        return self._model

    def parent(self):
        assert self._parent is not self
        return self._parent

    def data(self, role=Qt.DisplayRole, column=0):
        if role == ItemRole:
            return QVariant(self)
        else:
            return QVariant()

    def flags(self, column):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def setData(self, value, role=Qt.DisplayRole, column=0):
        return False

    def getPosOfChild(self, item):
        return self._children.index(item)

    def getChildAt(self, pos):
        return self._children[pos]

    def getPreviousSibling(self):
        p = self.parent()
        if p is not None:
            row = p.getPosOfChild(self)
            if row > 0:
                return p.getChildAt(row-1)
        return None

    def getNextSibling(self):
        p = self.parent()
        if p is not None:
            row = p.getPosOfChild(self)
            if row < len(p.children()) - 1:
                return p.getChildAt(row+1)
        return None

    def _attachToModel(self, model, indices):
        assert self.model() is None
        assert not self._pindex
        assert self.parent() is not None
        assert self.parent().model() is not None

        self._model = model

        for i in range(self.model().columnCount()):
            if i < self._columns:
                ind = indices[i]
            else:
                ind = QModelIndex()
            self._pindex.append(QPersistentModelIndex(ind))

        # Recurse
        for i in range(len(self.children())):
            item = self.children()[i]
            cindices = [self.model().createIndex(i, j, item) for j in range(item._columns)]
            item._attachToModel(model, cindices)

    def pindex(self, column=0):
        assert self._pindex
        return self._pindex[column]

    def index(self, column=0):
        assert self._pindex
        return QModelIndex(self._pindex[column])

    def appendChild(self, item):
        assert isinstance(item, ModelItem)
        assert item.model() is None
        assert item.parent() is None

        if self.model() is not None:
            next_row = len(self._children)
            self.model().beginInsertRows(self.index(), next_row, next_row)

        item._parent = self
        self.children().append(item)

        if self.model() is not None:
            indices = [self.model().createIndex(next_row, i, item) for i in range(item._columns)]
            item._attachToModel(self.model(), indices)
            self.model().endInsertRows()

    def appendChildren(self, items):
        for item in items:
            assert isinstance(item, ModelItem)
            assert item.model() is None
            assert item.parent() is None

        if self.model() is not None:
            next_row = len(self._children)
            self.model().beginInsertRows(self.index(), next_row, next_row + len(items) - 1)

        for item in items:
            item._parent = self
            self.children().append(item)

        if self.model() is not None:
            for i in range(len(items)):
                item = items[i]
                indices = [self.model().createIndex(next_row+i, j, item) for j in range(item._columns)]
                item._attachToModel(self.model(), indices)

            self.model().endInsertRows()

    def deleteAllChildren(self, notifyModel=True):
        if notifyModel and self._model is not None:
            self._model.beginRemoveRows(self.index(), 0, len(self._children) - 1)
        for child in self._children:
            child.deleteAllChildren(notifyModel=False)
        self._children = []
        if notifyModel and self._model is not None:
            self._model.endRemoveRows()

    def delete(self):
        if self.parent() is None:
            raise RuntimeError("Trying to delete orphan")
        else:
            self.parent().deleteChild(self)

    def deleteChild(self, arg, notifyModel=True):
        if isinstance(arg, ModelItem):
            self.deleteChild(self._children.index(arg))
        else:
            if arg < 0 or arg >= len(self._children):
                raise IndexError("child index out of range")
            if notifyModel and self._model is not None:
                self._model.beginRemoveRows(self.index(), arg, arg)
            self._children[arg].deleteAllChildren(notifyModel=False)
            del self._children[arg]
            if notifyModel and self._model is not None:
                self._model.endRemoveRows()

class RootModelItem(ModelItem):
    def __init__(self, model):
        ModelItem.__init__(self)
        self._model = model
        self._pindex = [QPersistentModelIndex() for i in range(model.columnCount())]

    def appendChild(self, item):
        if isinstance(item, FileModelItem):
            ModelItem.appendChild(self, item)
        else:
            raise TypeError("Only FileModelItems can be attached to RootModelItem")

    def appendFileItem(self, fileinfo):
        item = FileModelItem.create(fileinfo)
        self.appendChild(item)

    def appendFileItems(self, fileinfos):
        items = [FileModelItem.create(fi) for fi in fileinfos]
        self.appendChildren(items)

    def numFiles(self):
        return len(self.children())

    def numAnnotations(self):
        # TODO
        return 0

    def getAnnotations(self):
        return [child.getAnnotations() for child in self.children()]

class FileModelItem(ModelItem):
    def __init__(self, fileinfo):
        ModelItem.__init__(self)
        self.update(fileinfo)

    def data(self, role=Qt.DisplayRole, column=0):
        if role == Qt.DisplayRole and column == 0:
            return os.path.basename(self['filename'])
        return ModelItem.data(self, role, column)

    @staticmethod
    def create(fileinfo):
        if fileinfo['type'] == 'image':
            return ImageFileModelItem(fileinfo)
        elif fileinfo['type'] == 'video':
            return VideoFileModelItem(fileinfo)

class ImageModelItem(ModelItem):
    def __init__(self, annotations):
        ModelItem.__init__(self)
        for ann in annotations:
            self.addAnnotation(ann)

    def addAnnotation(self, ann):
        self.appendChild(AnnotationModelItem(ann))

    def removeAnnotation(self, pos):
        self.deleteChild(pos)

    def updateAnnotation(self, ann):
        for child in self._children:
            if child.type() == ann['type']:
                if (child.has_key('id') and ann.has_key('id') and child['id'] == ann['id']) or (not child.has_key('id') and not ann.has_key('id')):
                    ann[None] = None
                    child.setData(QVariant(ann), DataRole, 1)
                    return
        raise Exception("No AnnotationModelItem found that could be updated!")

class KeyValueModelItem(ModelItem):
    def __init__(self, hidden=[]):
        ModelItem.__init__(self)
        self._items = {}
        self._hidden = hidden
        # dummy key/value so that pyqt does not convert the dict
        # into a QVariantMap while communicating with the Views
        self[None] = None

    def _valueChanged(self):
        # Keep self._dict and self._items in sync
        for key, val in self._items.iteritems():
            if not key in self:
                self.deleteChild(val)

        for key, val in self.iteritems():
            if not key in self._items and key is not None and key not in self._hidden:
                self._items[key] = KeyValueRowModelItem(key)
                self.appendChild(self._items[key])

        if self.model() is not None:
            # TODO: Emit for hidden key/values?
            self.model().dataChanged.emit(self.index(), self.index())

class ImageFileModelItem(FileModelItem, ImageModelItem, KeyValueModelItem):
    def __init__(self, fileinfo):
        annotations = fileinfo.get("annotations", [])
        if fileinfo.has_key("annotations"):
            del fileinfo["annotations"]
        KeyValueModelItem.__init__(self, hidden=('filename', 'type'))
        FileModelItem.__init__(self, fileinfo)
        ImageModelItem.__init__(self, annotations)

    def data(self, role=Qt.DisplayRole, column=0):
        if role == DataRole:
            return self._fileinfo
        return FileModelItem.data(self, role)

    def getAnnotations(self):
        fi = copy.deepcopy(self._fileinfo)
        fi['annotations'] = [child.getAnnotations() for child in self.children()]
        return fi

class VideoFileModelItem(FileModelItem):
    def __init__(self, fileinfo):
        frameinfos = fileinfo.get("frames", [])
        if fileinfo.has_key("frames"):
            del fileinfo["frames"]
        FileModelItem.__init__(self, fileinfo)

        for frameinfo in frameinfos:
            self.appendChild(FrameModelItem(frameinfo))

    def getAnnotations(self):
        fi = copy.deepcopy(self._fileinfo)
        fi['frames'] = [child.getAnnotations() for child in self.children()]
        return fi

class FrameModelItem(ImageModelItem, KeyValueModelItem):
    def __init__(self, frameinfo):
        annotations = frameinfo.get("annotations", [])
        if frameinfo.has_key("annotations"):
            del frameinfo["annotations"]
        KeyValueModelItem.__init__(self)
        ImageModelItem.__init__(self, annotations)
        self.update(frameinfo)

    def framenum(self):
        return int(self.get('num', -1))

    def timestamp(self):
        return float(self.get('timestamp', -1))

    def data(self, role=Qt.DisplayRole, column=0):
        if role == Qt.DisplayRole and column == 0:
            return "%d / %.3f" % (self.framenum(), self.timestamp())
        return ImageModelItem.data(self, role, column)

    def getAnnotations(self):
        fi = copy.deepcopy(self._frameinfo)
        fi['annotations'] = [child.getAnnotations() for child in self.children()]
        return fi

class AnnotationModelItem(KeyValueModelItem):
    def __init__(self, annotation):
        KeyValueModelItem.__init__(self)
        # dummy key/value so that pyqt does not convert the dict
        # into a QVariantMap while communicating with the Views
        self[None] = None
        self.update(annotation)

    # Delegated from QAbstractItemModel
    def data(self, role=Qt.DisplayRole, column=0):
        if role == Qt.DisplayRole and column == 0:
            return self['type']
        elif role == TypeRole:
            return self['type']
        elif role == DataRole:
            return self._annotation
        return ModelItem.data(self, role, column)

class KeyValueRowModelItem(ModelItem):
    def __init__(self, key):
        ModelItem.__init__(self)
        self._key = key
        self._columns = 2

    def key(self):
        return self._key

    def data(self, role=Qt.DisplayRole, column=0):
        if role == Qt.DisplayRole:
            if column == 0:
                return self._key
            elif column == 1:
                return QVariant(self.parent()[self._key])
            else:
                return QVariant()
        else:
            return ModelItem.data(self, role, column)

    def flags(self, column):
        return Qt.NoItemFlags

class AnnotationModel(QAbstractItemModel):
    # signals
    dirtyChanged = pyqtSignal(bool, name='dirtyChanged')

    def __init__(self, annotations, parent=None):
        QAbstractItemModel.__init__(self, parent)
        self._annotations = annotations
        self._dirty       = False
        self._root        = RootModelItem(self)
        self._root.appendFileItems(annotations)

    # QAbstractItemModel overloads
    def columnCount(self, index=QModelIndex()):
        return 2

    def rowCount(self, index=QModelIndex()):
        item = self.itemFromIndex(index)
        return len(item.children())

    def parent(self, index):
        if index is None:
            return QModelIndex()
        item = self.itemFromIndex(index)
        parent = item.parent()
        if parent is None:
            return QModelIndex()
        return parent.index()

    def index(self, row, column, parent_idx=QModelIndex()):
        parent = self.itemFromIndex(parent_idx)
        if row >= len(parent.children()):
            return QModelIndex()
        return parent.children()[row].index(column)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        item = self.itemFromIndex(index)
        return item.data(role, index.column())

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        item = self.itemFromIndex(index)
        return item.setData(value, role, index.column())

    def flags(self, index):
        if not index.isValid():
            return self._root.flags(index.column())
        item = self.itemFromIndex(index)
        return item.flags(index.column())

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:   return QVariant("File/Type/Key")
            elif section == 1: return QVariant("Value")
        return QVariant()

    # Own methods
    def root(self):
        return self._root

    def dirty(self):
        return self._dirty

    # TODO: This might need to be updated from within the ModelItems when they change
    def setDirty(self, dirty=True):
        if dirty != self._dirty:
            self._dirty = dirty
            self.dirtyChanged.emit(self._dirty)

    def itemFromIndex(self, index):
        index = QModelIndex(index)  # explicitly convert from QPersistentModelIndex
        if index.isValid():
            return index.internalPointer()
        return self._root


#######################################################################################
# proxy model
#######################################################################################

class AnnotationSortFilterProxyModel(QSortFilterProxyModel):
    """Adds sorting and filtering support to the AnnotationModel without basically
    any implementation effort.  Special functions such as ``insertPoint()`` just
    call the source models respective functions."""
    def __init__(self, parent=None):
        super(AnnotationSortFilterProxyModel, self).__init__(parent)

    def fileIndex(self, index):
        fi = self.sourceModel().fileIndex(self.mapToSource(index))
        return self.mapFromSource(fi)

    def itemFromIndex(self, index):
        return self.sourceModel().itemFromIndex(self.mapToSource(index))

    def baseDir(self):
        return self.sourceModel().baseDir()

    def insertPoint(self, pos, parent, **kwargs):
        return self.sourceModel().insertPoint(pos, self.mapToSource(parent), **kwargs)

    def insertRect(self, rect, parent, **kwargs):
        return self.sourceModel().insertRect(rect, self.mapToSource(parent), **kwargs)

    def insertMask(self, fname, parent, **kwargs):
        return self.sourceModel().insertMask(fname, self.mapToSource(parent), **kwargs)

    def insertFile(self, filename):
        return self.sourceModel().insertFile(filename)


#######################################################################################
# view
#######################################################################################

class AnnotationTreeView(QTreeView):
    selectedItemsChanged = pyqtSignal(object)

    def __init__(self, parent=None):
        super(AnnotationTreeView, self).__init__(parent)

        self.setUniformRowHeights(True)
        self.setSelectionMode(QTreeView.ExtendedSelection)
        self.setSelectionBehavior(QTreeView.SelectItems)
        self.setAllColumnsShowFocus(True)
        self.setAlternatingRowColors(True)
        #self.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.setSortingEnabled(True)
        self.expanded.connect(self.onExpanded)

    def resizeColumns(self):
        for column in range(self.model().columnCount(QModelIndex())):
            self.resizeColumnToContents(column)

    def onExpanded(self):
        self.resizeColumns()

    def setModel(self, model):
        QTreeView.setModel(self, model)
        self.resizeColumns()

    def rowsInserted(self, index, start, end):
        QTreeView.rowsInserted(self, index, start, end)
        self.resizeColumns()

    def setSelectedItems(self, items):
        block = self.blockSignals(True)
        sel = QItemSelection()
        for item in items:
            sel.merge(QItemSelection(item.index(), item.index()), QItemSelectionModel.SelectCurrent)
        self.selectionModel().clear()
        self.selectionModel().select(sel, QItemSelectionModel.Select)
        self.blockSignals(block)

    def selectionChanged(self, selected, deselected):
        items = [ self.model().itemFromIndex(index) for index in self.selectionModel().selectedIndexes()]
        self.selectedItemsChanged.emit(items)
        QTreeView.selectionChanged(self, selected, deselected)
