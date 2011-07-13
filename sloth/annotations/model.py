"""
The annotationmodel module contains the classes for the AnnotationModel.
"""
from PyQt4.QtGui import QTreeView, QItemSelection, QItemSelectionModel, QSortFilterProxyModel, QBrush
from PyQt4.QtCore import QModelIndex, QAbstractItemModel, Qt, pyqtSignal, QVariant
import os.path
import copy
from collections import MutableMapping
import time
import logging
LOG = logging.getLogger(__name__)

ItemRole, DataRole, ImageRole = [Qt.UserRole + i + 1 for i in range(3)]

class ModelItem:
    def __init__(self):
        self._loaded    = True
        self._model     = None
        self._parent    = None
        self._row       = -1
        if not hasattr(self, "_children"):
            self._children = []

    def _load(self, index):
        pass

    def _ensureLoaded(self, index):
        if not self._loaded:
            if not isinstance(self._children[index], ModelItem):
                # Need to set the before actually loading to avoid
                # endless recursion...
                self._load(index)
                return True
        return False

    def _ensureAllLoaded(self):
        if not self._loaded:
            for i in range(len(self._children)-1):
                self._ensureLoaded(i)
            return True
        return False

    def hasChildren(self):
        return len(self._children) > 0

    def childHasChildren(self, row):
        return self.childAt(row).hasChildren()

    def rowCount(self):
        return len(self._children)

    def childRowCount(self, pos):
        return self.childAt(pos).rowCount()

    def children(self):
        if self._ensureAllLoaded():
            LOG.debug("Loaded because of call to children()")
        return self._children

    def model(self):
        return self._model

    def parent(self):
        return self._parent

    def data(self, role=Qt.DisplayRole, column=0):
        if role == Qt.DisplayRole:
            return ""
        if role == Qt.BackgroundRole:
            c = self.getColor()
            if c is not None:
                return QBrush(c)
        if role == ItemRole:
            return self
        else:
            return None

    def childData(self, role=Qt.DisplayRole, row=0, column=0):
        return self.childAt(row).data(role, column)

    def flags(self, column):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def childFlags(self, row, column):
        return self.childAt(row).flags(column)

    def setData(self, value, role=Qt.DisplayRole, column=0):
        return False

    def childAt(self, pos):
        if self._ensureLoaded(pos):
            LOG.debug("Loaded child at %d because of call to childAt()" % pos)
        return self._children[pos]

    def getPreviousSibling(self):
        if self._parent is not None:
            if self._row > 0:
                return self._parent.childAt(self._row-1)
        return None

    def getNextSibling(self):
        if self._parent is not None:
            try:
                return self._parent.childAt(self._row+1)
            except:
                pass
        return None

    def _attachToModel(self, model):
        #assert self.model() is None
        #assert self.parent() is not None
        #assert self.parent().model() is not None

        self._model = model
        for item in self._children:
            if isinstance(item, ModelItem):
                item._attachToModel(model)

    def index(self, column=0):
        if self._parent is None:
            return QModelIndex()
        if column >= self._model.columnCount():
            return QModelIndex()
        return self._model.createIndex(self._row, column, self._parent)

    def addChildSorted(self, item, signalModel=True):
        self.insertChild(-1, item, signalModel=signalModel)

    def appendChild(self, item, signalModel=True):
        self.insertChild(-1, item, signalModel=signalModel)

    def replaceChild(self, pos, item):
        item._parent = self
        item._row    = pos
        self._children[pos] = item
        if self._model is not None:
            self._children[pos]._attachToModel(self._model)

    def insertChild(self, pos, item, signalModel=True):
        if pos >= 0:
            next_row = pos
        else:
            next_row = len(self._children)
        if self._model is not None and signalModel:
            self._model.beginInsertRows(self.index(), next_row, next_row)

        item._parent = self
        item._row    = next_row
        self._children.insert(next_row, item)

        if pos >= 0:
            for i, c in enumerate(self._children):
                c._row = i

        if self._model is not None:
            item._attachToModel(self._model)
            if signalModel:
                self._model.endInsertRows()

    def appendChildren(self, items, signalModel=True):
        #for item in items:
            #assert isinstance(item, ModelItem)
            #assert item.model() is None
            #assert item.parent() is None

        next_row = len(self._children)
        if self._model is not None and signalModel:
            self._model.beginInsertRows(self.index(), next_row, next_row + len(items) - 1)

        for i, item in enumerate(items):
            item._parent = self
            item._row    = next_row + i
            self._children.append(item)

        if self._model is not None:
            for item in items:
                item._attachToModel(self._model)
            if signalModel:
                self._model.endInsertRows()

    def delete(self):
        if self._parent is None:
            raise RuntimeError("Trying to delete orphan")
        else:
            self._parent.deleteChild(self)

    def deleteChild(self, arg):
        # Grandchildren are considered deleted automatically
        if isinstance(arg, ModelItem):
            return self.deleteChild(self._children.index(arg))
        else:
            if arg < 0 or arg >= len(self._children):
                raise IndexError("child index out of range")
            if self._ensureLoaded(arg):
                LOG.debug("Loaded because of call to deleteChild()")

            if self._model is not None:
                self._model.beginRemoveRows(self.index(), arg, arg)

            del self._children[arg]

            # Update cached row numbers
            for i, c in enumerate(self._children):
                c._row = i

            if self._model is not None:
                self._model.endRemoveRows()

    def deleteAllChildren(self):
        if self._ensureAllLoaded():
            LOG.debug("Loaded because of call to deleteAllChildren()")
        if self._model is not None:
            self._model.beginRemoveRows(self.index(), 0, len(self._children) - 1)

        self._children = []

        if self._model is not None:
            self._model.endRemoveRows()

    def getColor(self):
        return None

class RootModelItem(ModelItem):
    def __init__(self, model, files):
        ModelItem.__init__(self)
        self._model = model
        self._toload   = []
        for f in files:
            self._toload.append(f)
            self._children.append(f)
        self._loaded = False

    def _load(self, index):
        LOG.debug("Loading data for RootModelItem pos %d" % index)
        self._toload.remove(self._children[index])
        fi = FileModelItem.create(self._children[index])
        self.replaceChild(index, fi)
        if len(self._toload) == 0:
            self._loaded = True

    def childHasChildren(self, pos):
        if isinstance(self._children[pos], ModelItem):
            return self._children[pos].hasChildren()
        else:
            # Hack to speed things up...
            return True

    def childFlags(self, row, column):
        if isinstance(self._children[row], ModelItem):
            return self._children[row].flags(column)
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def appendChild(self, item):
        if isinstance(item, FileModelItem):
            ModelItem.appendChild(self, item)
        else:
            raise TypeError("Only FileModelItems can be attached to RootModelItem")

    def appendFileItem(self, fileinfo):
        item = FileModelItem.create(fileinfo)
        self.appendChild(item)

    def appendFileItems(self, fileinfos):
        start1 = time.time()
        items = [FileModelItem.create(fi) for fi in fileinfos]
        diff1 = time.time() - start1
        start2 = time.time()
        self.appendChildren(items)
        diff2 = time.time() - start2
        LOG.debug("Creation of ModelItems: %.2fs, addition to model: %.2fs" % (diff1, diff2))

    def numFiles(self):
        return 0
        return len(self.children())

    def numAnnotations(self):
        return 0
        count = 0
        for ann in self._model.iterator(AnnotationModelItem):
            count += 1
        return count

    def getAnnotations(self):
        return [child.getAnnotations() for child in self.children()]

class KeyValueModelItem(ModelItem, MutableMapping):
    def __init__(self, hidden=[], properties=None):
        ModelItem.__init__(self)
        self._dict   = {}
        self._items  = {}
        self._hidden = hidden + [None, 'class', 'unlabeled', 'unconfirmed']
        # dummy key/value so that pyqt does not convert the dict
        # into a QVariantMap while communicating with the Views
        self._dict[None] = None
        if properties is not None:
            self._dict.update(properties)
            for key in self._dict.keys():
                if key not in self._hidden:
                    item = KeyValueRowModelItem(key)
                    self._items[key] = item
                    self.addChildSorted(item)

    def addChildSorted(self, item, signalModel=True):
        if isinstance(item, KeyValueRowModelItem):
            next_row = 0
            for child in self._children:
                if not isinstance(child, KeyValueRowModelItem) or child.key() > item.key():
                    break
                next_row += 1

            self.insertChild(next_row, item, signalModel)
        else:
            self.appendChild(item, signalModel)

    # Methods for MutableMapping
    def __len__(self):
        return len(self._dict)

    def __iter__(self):
        return iter(self._dict.keys())

    def __getitem__(self, key):
        return self._dict[key]

    def _emitDataChanged(self, key):
        if self.model() is not None:
            if key in self._items:
                index_tl = self._items[key].index()
                index_br = self._items[key].index(1)
            else:
                index_tl = self.index()
                index_br = self.index(1)
            self.model().dataChanged.emit(index_tl, index_br)

    def __setitem__(self, key, value):
        if key not in self._dict:
            self._dict[key] = value
            if key not in self._hidden:
                self._items[key] = KeyValueRowModelItem(key)
                self.addChildSorted(self._items[key])
        elif self._dict[key] != value:
            self._dict[key] = value
            # TODO: Emit for hidden key/values?
            self._emitDataChanged(key)

    def __delitem__(self, key):
        del self._dict[key]
        if key in self._items:
            self.deleteChild(self._items[key])

    def has_key(self, key):
        return key in self._dict

    def clear(self):
        if len(self._dict) > 0:
            MutableMapping.clear(self)

    def getAnnotations(self):
        res = copy.deepcopy(self._dict)
        if None in res: del res[None]
        return res

    def isUnlabeled(self):
        return 'unlabeled' in self._dict and self._dict['unlabeled']

    def setUnlabeled(self, val):
        if val:
            self._dict['unlabeled'] = val
        else:
            if 'unlabeled' in self._dict:
                del self['unlabeled']
                self._emitDataChanged('unlabeled')

    def isUnconfirmed(self):
        return 'unconfirmed' in self._dict and self._dict['unconfirmed']

    def setUnconfirmed(self, val):
        if val:
            self._dict['unconfirmed'] = val
        else:
            if 'unconfirmed' in self._dict:
                del self['unconfirmed']
                self._emitDataChanged('unconfirmed')

class FileModelItem(KeyValueModelItem):
    def __init__(self, fileinfo, hidden=['filename']):
        KeyValueModelItem.__init__(self, hidden=hidden, properties=fileinfo)

    def data(self, role=Qt.DisplayRole, column=0):
        if role == Qt.DisplayRole:
            if column == 0:
                return os.path.basename(self['filename'])
            elif column == 1 and self.isUnlabeled():
                return '[unlabeled]'
        return ModelItem.data(self, role, column)

    def getColor(self):
        if self.isUnlabeled():
            return Qt.red
        return None

    @staticmethod
    def create(fileinfo):
        if fileinfo['class'] == 'image':
            return ImageFileModelItem(fileinfo)
        elif fileinfo['class'] == 'video':
            return VideoFileModelItem(fileinfo)

class ImageModelItem(ModelItem):
    def __init__(self, annotations):
        ModelItem.__init__(self)
        for ann in annotations:
            self.addAnnotation(ann)

    def addAnnotation(self, ann, signalModel=True):
        self.addChildSorted(AnnotationModelItem(ann), signalModel=signalModel)

    def annotations(self):
        for child in self._children:
            if isinstance(child, AnnotationModelItem):
                yield child

    def confirmAll(self):
        for ann in self.annotations():
            ann.setUnconfirmed(False)

class ImageFileModelItem(FileModelItem, ImageModelItem):
    def __init__(self, fileinfo):
        self._annotation_data = fileinfo.get("annotations", [])
        if "annotations" in fileinfo:
            del fileinfo["annotations"]
        FileModelItem.__init__(self, fileinfo)
        ImageModelItem.__init__(self, [])
        self._toload = []
        for ann in self._annotation_data:
            self._children.append(ann)
            self._toload.append(ann)
        self._loaded = False

    def _load(self, index):
        LOG.debug("Loading data for ImageFileModelItem %s pos %d" % (self['filename'], index))
        self._toload.remove(self._children[index])
        ann = AnnotationModelItem(self._children[index])
        self.replaceChild(index, ann)
        if len(self._toload) == 0:
            self._loaded = True

    def data(self, role=Qt.DisplayRole, column=0):
        if role == DataRole:
            return self._dict
        return FileModelItem.data(self, role, column)

    def getAnnotations(self):
        if self._ensureLoaded():
            LOG.debug("Loaded because of call to getAnnotations()")
        fi = KeyValueModelItem.getAnnotations(self)
        fi['annotations'] = [child.getAnnotations() for child in self.children()]
        return fi

class VideoFileModelItem(FileModelItem):
    def __init__(self, fileinfo):
        frameinfos = fileinfo.get("frames", [])
        if "frames" in fileinfo:
            del fileinfo["frames"]
        FileModelItem.__init__(self, fileinfo)

        for frameinfo in frameinfos:
            self.addChildSorted(FrameModelItem(frameinfo))

    def getAnnotations(self):
        fi = KeyValueModelItem.getAnnotations(self)
        fi['frames'] = [child.getAnnotations() for child in self.children()]
        return fi

class FrameModelItem(ImageModelItem, KeyValueModelItem):
    def __init__(self, frameinfo):
        annotations = frameinfo.get("annotations", [])
        if "annotations" in frameinfo:
            del frameinfo["annotations"]
        KeyValueModelItem.__init__(self, properties=frameinfo)
        ImageModelItem.__init__(self, annotations)

    def framenum(self):
        return int(self.get('num', -1))

    def timestamp(self):
        return float(self.get('timestamp', -1))

    def data(self, role=Qt.DisplayRole, column=0):
        if role == Qt.DisplayRole:
            if column == 0:
                return "%d / %.3f" % (self.framenum(), self.timestamp())
            elif column == 1 and self.isUnlabeled():
                return '[unlabeled]'
        return ImageModelItem.data(self, role, column)

    def getColor(self):
        if self.isUnlabeled():
            return Qt.red
        return None

    def getAnnotations(self):
        fi = KeyValueModelItem.getAnnotations(self)
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
        if role == Qt.DisplayRole:
            if column == 0:
                return self['class']
            elif column == 1 and self.isUnconfirmed():
                return '[unconfirmed]'
            else:
                return ""
        elif role == DataRole:
            return self._annotation
        return ModelItem.data(self, role, column)

    def getColor(self):
        if self.isUnconfirmed():
            return Qt.red
        return None

class KeyValueRowModelItem(ModelItem):
    def __init__(self, key, read_only=True):
        ModelItem.__init__(self)
        self._key = key
        self._read_only = read_only

    def key(self):
        return self._key

    def data(self, role=Qt.DisplayRole, column=0):
        if role == Qt.DisplayRole:
            if column == 0:
                return self._key
            elif column == 1:
                return self.parent()[self._key]
            else:
                return None
        else:
            return ModelItem.data(self, role, column)

    def flags(self, column):
        if self._read_only:
            return Qt.NoItemFlags
        else:
            if column == 1:
                return Qt.ItemIsEnabled | Qt.ItemIsEditable
            else:
                return Qt.ItemIsEnabled

    def setData(self, value, role=Qt.DisplayRole, column=0):
        if column == 1:
            if isinstance(value, QVariant):
                value = value.toPyObject()
            self._parent[self._key] = value
            return True
        return False

class AnnotationModel(QAbstractItemModel):
    # signals
    dirtyChanged = pyqtSignal(bool, name='dirtyChanged')

    def __init__(self, annotations, parent=None):
        QAbstractItemModel.__init__(self, parent)
        start = time.time()
        self._annotations = annotations
        self._dirty       = False
        self._root        = RootModelItem(self, annotations)
        diff = time.time() - start
        LOG.info("Created AnnotationModel in %.2fs" % (diff, ))
        self.dataChanged.connect(self.onDataChanged)
        self.rowsInserted.connect(self.onDataChanged)
        self.rowsRemoved.connect(self.onDataChanged)

    # QAbstractItemModel overloads
    def hasChildren(self, index=QModelIndex()):
        if index.column() > 0:
            return 0
        if not index.isValid():
            return self._root.hasChildren()

        parent = self.parentFromIndex(index)
        return parent.childHasChildren(index.row())

    def columnCount(self, index=QModelIndex()):
        return 2

    def rowCount(self, index=QModelIndex()):
        # Only items with column==1 can have children
        if index.column() > 0:
            return 0
        if not index.isValid():
            return self._root.rowCount()

        parent = self.parentFromIndex(index)
        return parent.childRowCount(index.row())

    def parent(self, index):
        if index is None:
            return QModelIndex()
        return self.parentFromIndex(index).index()

    def index(self, row, column, parent_idx=QModelIndex()):
        # Handle invalid rows/columns
        if row < 0 or column < 0:
            return QModelIndex()

        # Only items with column == 0 can have children
        if parent_idx.isValid() and parent_idx.column() > 0:
            return QModelIndex()

        # Handle root item
        if parent_idx == QModelIndex():
            parent = self._root
        # Handle normal items
        else:
            parent = self.itemFromIndex(parent_idx)
        if row < 0 or row >= parent.rowCount():
            return QModelIndex()
        if column < 0 or column >= self.columnCount():
            return QModelIndex()
        return self.createIndex(row, column, parent)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        parent = self.parentFromIndex(index)
        return parent.childData(role, index.row(), index.column())

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        item = self.itemFromIndex(index)
        return item.setData(value, role, index.column())

    def flags(self, index):
        if not index.isValid():
            return self._root.flags(index.column())
        parent = self.parentFromIndex(index)
        return parent.childFlags(index.row(), index.column())

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:   return "File/Type/Key"
            elif section == 1: return "Value"
        return None

    # Own methods
    def root(self):
        return self._root

    def dirty(self):
        return self._dirty

    def setDirty(self, dirty=True):
        if dirty != self._dirty:
            LOG.debug("Setting model state to dirty")
            self._dirty = dirty
            self.dirtyChanged.emit(self._dirty)

    def onDataChanged(self, *args):
        self.setDirty()

    def itemFromIndex(self, index):
        index = QModelIndex(index)  # explicitly convert from QPersistentModelIndex
        if index.isValid():
            return index.internalPointer().childAt(index.row())
        return self._root

    def parentFromIndex(self, index):
        index = QModelIndex(index)  # explicitly convert from QPersistentModelIndex
        if index.isValid():
            return index.internalPointer()
        return self._root

    def iterator(self, _class=None, predicate=None, start=None, maxlevels=10000):
        # Visit all nodes
        level = 0
        item = start if start is not None else self.root()
        while item is not None:
            # Return item
            if _class is None or isinstance(item, _class):
                if predicate is None or predicate(item):
                    yield item

            # Get next item
            if item.rowCount() > 0 and level < maxlevels:
                level += 1
                item = item.childAt(0)
            else:
                next_sibling = item.getNextSibling()
                if next_sibling is not None:
                    item = next_sibling
                else:
                    level -= 1
                    ancestor = item.parent()
                    item = None
                    while ancestor is not None:
                        ancestor_sibling = ancestor.getNextSibling()
                        if ancestor_sibling is not None:
                            item = ancestor_sibling
                            break
                        level -= 1
                        ancestor = ancestor.parent()


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
        self.setSelectionBehavior(QTreeView.SelectRows)
        self.setAllColumnsShowFocus(True)
        self.setAlternatingRowColors(True)
        #self.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.setSortingEnabled(True)
        self.setAnimated(True)
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
            sel.merge(QItemSelection(item.index(), item.index(1)), QItemSelectionModel.SelectCurrent)
        self.selectionModel().clear()
        self.selectionModel().select(sel, QItemSelectionModel.Select)
        self.blockSignals(block)

    def selectionChanged(self, selected, deselected):
        items = [ self.model().itemFromIndex(index) for index in self.selectionModel().selectedIndexes()]
        self.selectedItemsChanged.emit(items)
        QTreeView.selectionChanged(self, selected, deselected)
