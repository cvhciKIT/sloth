"""
The annotationmodel module contains the classes for the AnnotationModel.
"""
from PyQt4.QtGui import QTreeView, QSortFilterProxyModel, QAbstractItemView
from PyQt4.QtCore import QModelIndex, QPersistentModelIndex, QAbstractItemModel, QVariant, Qt, pyqtSignal
import os.path

ItemRole, TypeRole, DataRole, ImageRole = [Qt.UserRole + i + 1 for i in range(4)]

class ModelItem:
    def __init__(self):
        self._children = []
        self._pindex   = []
        self._model    = None
        self._parent   = None
        self._columns  = 1

    def children(self):
        return self._children

    def model(self):
        return self._model

    def parent(self):
        assert self._parent != self
        return self._parent

    def data(self, role=Qt.DisplayRole, column=0):
        if role == ItemRole:
            return QVariant(self)
        else:
            return QVariant()

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
            if row < len(p.children()) - 2:
                return p.getChildAt(row+1)
        return None

    def _attachToModel(self, model):
        assert self.model() is None
        assert not self._pindex
        assert self.parent() is not None
        assert self.parent().model() is not None

        self._model = model
        p = self.parent()

        # Find out own index
        for i in range(self.model().columnCount()):
            if i < self._columns:
                index = self.model().createIndex(p.getPosOfChild(self), i, self)
            else:
                index = QModelIndex()
            self._pindex.append(QPersistentModelIndex(index))

        # Recurse
        for item in self.children():
            item._attachToModel(model)

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
            item._attachToModel(self.model())
            self.model().endInsertRows()

    def deleteAllChildren(self):
        for child in self._children:
            child.deleteAllChildren()

        self._model.beginRemoveRows(self.index(), 0, len(self._children) - 1)
        self._children = []
        self._model.endRemoveRows()

    def delete(self):
        if self.parent() is None:
            raise RuntimeError("Trying to delete orphan")
        else:
            self.parent().deleteChild(self)

    def deleteChild(self, arg):
        if isinstance(arg, ModelItem):
            self.deleteChild(self._children.index(arg))
        else:
            if arg < 0 or arg >= len(self._children):
                raise IndexError("child index out of range")
            self._children[arg].deleteAllChildren()
            self._model.beginRemoveRows(self.index(), arg, arg)
            del self._children[arg]
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
        for fileinfo in fileinfos:
            self.appendFileItem(fileinfo)

class FileModelItem(ModelItem):
    def __init__(self, fileinfo):
        ModelItem.__init__(self)
        self._fileinfo = fileinfo

    def filename(self):
        return self._fileinfo['filename']

    def data(self, role=Qt.DisplayRole, column=0):
        if role == Qt.DisplayRole and column == 0:
            return os.path.basename(self.filename())
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

    def appendChild(self, item):
        if isinstance(item, AnnotationModelItem):
            ModelItem.appendChild(self, item)
        else:
            raise TypeError("Only AnnotationModelItems can be attached to ImageModelItem")

    def addAnnotation(self, ann):
        self.appendChild(AnnotationModelItem(ann))

    def removeAnnotation(self, pos):
        self.deleteChild(pos)

    def updateAnnotation(self, ann):
        for child in self._children:
            if child.type() == ann['type']:
                if (child.has_key('id') and ann.has_key('id') and child.value('id') == ann['id']) or (not child.has_key('id') and not ann.has_key('id')):
                    ann[None] = None
                    child.setData(QVariant(ann), DataRole, 1)
                    return
        raise Exception("No AnnotationModelItem found that could be updated!")

class ImageFileModelItem(FileModelItem, ImageModelItem):
    def __init__(self, fileinfo):
        annotations = fileinfo.get("annotations", [])
        if fileinfo.has_key("annotations"):
            del fileinfo["annotations"]
        FileModelItem.__init__(self, fileinfo)
        ImageModelItem.__init__(self, annotations)

    def data(self, role=Qt.DisplayRole, column=0):
        if role == DataRole:
            return self._fileinfo
        return FileModelItem.data(self, role)

class VideoFileModelItem(FileModelItem):
    def __init__(self, fileinfo):
        frameinfos = fileinfo.get("frames", [])
        if fileinfo.has_key("frames"):
            del fileinfo["frames"]
        FileModelItem.__init__(self, fileinfo)

        for frameinfo in frameinfos:
            self.appendChild(FrameModelItem(frameinfo))

class FrameModelItem(ImageModelItem):
    def __init__(self, frameinfo):
        if frameinfo.has_key("annotations"):
            ImageModelItem.__init__(self, frameinfo["annotations"])
            del frameinfo["annotations"]
        self._frameinfo = frameinfo

    def framenum(self):
        return int(self._frameinfo.get('num', -1))

    def timestamp(self):
        return float(self._frameinfo.get('timestamp', -1))

    def data(self, role=Qt.DisplayRole, column=0):
        if role == Qt.DisplayRole and column == 0:
            return "%d / %.3f" % (self.framenum(), self.timestamp())
        return ImageModelItem.data(self, role, column)

class AnnotationModelItem(ModelItem):
    def __init__(self, annotation):
        ModelItem.__init__(self)
        self._annotation = annotation
        # dummy key/value so that pyqt does not convert the dict
        # into a QVariantMap while communicating with the Views
        self._annotation[None] = None

        for key, value in annotation.iteritems():
            if key == None:
                continue
            self.appendChild(KeyValueModelItem(key))

    def type(self):
        return self._annotation['type']

    def setData(self, value, role, column=0):
        if role == DataRole:
            print self._annotation
            value = value.toPyObject()
            print value, type(value)
            print self._annotation
            for key, val in value.iteritems():
                print key, val
                if not key in self._annotation:
                    print "not in annotation: ", key
                    self._annotation[key] = val
                    self.appendChild(KeyValueModelItem(key))

            for key in self._annotation.keys():
                if not key in value:
                    for child in [e for e in self.children() if e.key() == key]:
                        self.deleteChild(child)
                    del self._annotation[key]
                else:
                    self._annotation[key] = value[key]
                    if self.model() is not None:
                        for child in [e for e in self.children() if e.key() == key]:
                            self.model().dataChanged.emit(child.index(1), child.index(1))

            print "new annotation:", self._annotation
            return True
        return False

    def data(self, role=Qt.DisplayRole, column=0):
        if role == Qt.DisplayRole and column == 0:
            return self.type()
        elif role == TypeRole:
            return self.type()
        elif role == DataRole:
            return self._annotation
        return ModelItem.data(self, role, column)

    def setValue(self, key, value):
        self._annotation[key] = value
        if self.model() is not None:
            self.model().dataChanged.emit(self.index(), self.index())

    def value(self, key):
        return self._annotation[key]

    def has_key(self, key):
        return self._annotation.has_key(key)

class KeyValueModelItem(ModelItem):
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
                return self.parent().value(self._key)
            else:
                return QVariant()
        else:
            return ModelItem.data(self, role, column)

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
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:   return QVariant("File/Type/Key")
            elif section == 1: return QVariant("Value")
        return QVariant()

    # Own methods
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
    def __init__(self, parent=None):
        super(AnnotationTreeView, self).__init__(parent)

        self.setUniformRowHeights(True)
        self.setSelectionMode(QTreeView.SingleSelection)
        self.setSelectionBehavior(QTreeView.SelectItems)
        self.setAllColumnsShowFocus(True)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QAbstractItemView.SelectedClicked)
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

    def keyPressEvent(self, event):
        ## handle deletions of items
        if event.key() == Qt.Key_Delete:
            self.model().itemFromIndex(self.currentindex()).delete()

        ## it is important to use the keyPressEvent of QAbstractItemView, not QTreeView
        QAbstractItemView.keyPressEvent(self, event)

    def rowsInserted(self, index, start, end):
        QTreeView.rowsInserted(self, index, start, end)
        self.resizeColumns()
#        self.setCurrentIndex(index.child(end, 0))
