from PyQt4.QtGui import *
from PyQt4.QtCore import *
from functools import partial
import os.path
import okapy

DataRole, ImageRole = [Qt.UserRole + i for i in range(1,3)]

class ModelItem:
    def __init__(self, parent=None):
        self.parent_   = parent
        self.children_ = []

    def children(self):
        return self.children_

    def parent(self):
        return self.parent_

    def rowOfChild(self, item):
        try:
            return self.children_.index(item)
        except:
            return -1

    def data(self, index, role):
        return QVariant()

class RootModelItem(ModelItem):
    def __init__(self, files):
        ModelItem.__init__(self, None)
        self.files_ = files

        for file in files:
            fmi = FileModelItem.create(file, self)
            self.children_.append(fmi)

class FileModelItem(ModelItem):
    def __init__(self, file, parent):
        ModelItem.__init__(self, parent)
        self.file_ = file

    def filename(self):
        return self.file_['filename']

    def data(self, index, role):
        if role == Qt.DisplayRole and index.column() == 0:
            return os.path.basename(self.filename())
        return QVariant()

    @staticmethod
    def create(file, parent):
        if file['type'] == 'image':
            return ImageFileModelItem(file, parent)
        elif file['type'] == 'video':
            return VideoFileModelItem(file, parent)

class ImageFileModelItem(FileModelItem):
    def __init__(self, file, parent):
        FileModelItem.__init__(self, file, parent)

        for ann in file['annotations']:
            ami = AnnotationModelItem(ann, self)
            self.children_.append(ami)

    def data(self, index, role):
        if role == ImageRole:
            return okapy.loadImage(self.filename())
        return FileModelItem.data(self, index, role)

class VideoFileModelItem(FileModelItem):
    _cached_vs_filename = None
    _cached_vs          = None

    def __init__(self, file, parent):
        FileModelItem.__init__(self, file, parent)

        for frame in file['frames']:
            fmi = FrameModelItem(frame, self)
            self.children_.append(fmi)

    def updateCachedVideoSource(self):
        # have only one cached video source at a time for now
        # TODO: for labeling multiple synchronized videos this should
        # be modified, otherwise it might be awfully slow
        VideoFileModelItem._cached_vs = okv.ImageSequence()
        VideoFileModelItem._cached_vs.open(self.filename())
        VideoFileModelItem._cached_vs_filename = self.filename()

    def getFrame(self, frame):
        if VideoFileModelItem._cached_vs_filename != self.filename():
            self.updateCachedVideoSource()

        VideoFileModelItem._cached_vs.getFrame(frame)
        return VideoFileModelItem._cached_vs.getImage()

class FrameModelItem(ModelItem):
    def __init__(self, frame, parent):
        ModelItem.__init__(self, parent)
        self.frame_ = frame

        for ann in frame['annotations']:
            ami = AnnotationModelItem(ann, self)
            self.children_.append(ami)

    def framenum(self):
        return int(self.frame_.get('num', -1))

    def timestamp(self):
        return float(self.frame_.get('timestamp', -1))

    def addAnnotation(self, ann):
        self.frame_['annotations'].append(ann)
        ami = AnnotationModelItem(ann, self)
        self.children_.append(ami)

    def removeAnnotation(self, pos):
        del self.frame_['annotations'][pos]
        del self.children_[pos]

    def data(self, index, role):
        if role == Qt.DisplayRole and index.column() == 0:
            return "%d / %.3f" % (self.framenum(), self.timestamp())
        elif role == ImageRole:
            return self.parent().getFrame(self.frame_['num'])
        return QVariant()

class AnnotationModelItem(ModelItem):
    def __init__(self, annotation, parent):
        ModelItem.__init__(self, parent)
        self.annotation_ = annotation
        # dummy key/value so that pyqt does not convert the dict
        # into a QVariantMap while communicating with the Views
        self.annotation_[None] = None

        for key, value in annotation.iteritems():
            if key == None:
                continue
            self.children_.append(KeyValueModelItem(key, self))

    def type(self):
        return self.annotation_['type']

    def setData(self, index, value, role):
        if role == DataRole:
            self.annotation_ = value.toPyObject()
            #print "setData", self.annotation_
            index.model().dataChanged.emit(index, index.sibling(index.row(), 1))
            return True
        return False

    def data(self, index, role):
        if role == Qt.DisplayRole and index.column() == 0:
            return self.type()
        elif role == DataRole:
            #print "data():", self.annotation_
            return self.annotation_

        return QVariant()

    def value(self, key):
        return self.annotation_[key]

class KeyValueModelItem(ModelItem):
    def __init__(self, key, parent):
        ModelItem.__init__(self, parent)
        self.key_  = key

    def data(self, index, role):
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return self.key_
            elif index.column() == 1:
                return self.parent().value(self.key_)
            else:
                return QVariant()

class AnnotationModel(QAbstractItemModel):
    # signals
    dirtyChanged = pyqtSignal(bool, name='dirtyChanged')

    def __init__(self, annotations, parent=None):
        QAbstractItemModel.__init__(self, parent)
        self.annotations_ = annotations
        self.root_        = RootModelItem(self.annotations_)
        self.dirty_       = False

    def dirty(self):
        return self.dirty_

    def setDirty(self, dirty=True):
        previous = self.dirty_
        self.dirty_ = dirty
        if previous != dirty:
            self.dirtyChanged.emit(dirty)

    dirty = property(dirty, setDirty)

    def itemFromIndex(self, index):
        index = QModelIndex(index)  # explicitly convert from QPersistentModelIndex
        if index.isValid():
            return index.internalPointer()
        return self.root_

    def index(self, row, column, parent_idx):
        parent_item = self.itemFromIndex(parent_idx)
        if row >= len(parent_item.children()):
            return QModelIndex()
        child_item = parent_item.children()[row]
        return self.createIndex(row, column, child_item)

    def imageIndex(self, index):
        """return index that points to the (maybe parental) image/frame object"""
        if not index.isValid():
            return QModelIndex()

        index = QModelIndex(index)  # explicitly convert from QPersistentModelIndex
        item = self.itemFromIndex(index)
        if isinstance(item, ImageFileModelItem) or \
           isinstance(item, FrameModelItem):
            return index

        # try with next hierarchy up
        return self.imageIndex(index.parent())

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        index = QModelIndex(index)  # explicitly convert from QPersistentModelIndex

        #if role == Qt.CheckStateRole:
            #item = self.itemFromIndex(index)
            #if item.isCheckable(index.column()):
                #return QVariant(Qt.Checked if item.visible() else Qt.Unchecked)
            #return QVariant()

        #if role != Qt.DisplayRole and role != GraphicsItemRole and role != DataRole:
            #return QVariant()

        ## non decorational behaviour

        item = self.itemFromIndex(index)
        return item.data(index, role)

    def columnCount(self, index):
        return 2

    def rowCount(self, index):
        item = self.itemFromIndex(index)
        return len(item.children())

    def parent(self, index):
        item = self.itemFromIndex(index)
        parent = item.parent()
        if parent is None:
            return QModelIndex()
        grandparent = parent.parent()
        if grandparent is None:
            return QModelIndex()
        row = grandparent.rowOfChild(parent)
        assert row != -1
        return self.createIndex(row, 0, parent)

    def mapToSource(self, index):
        return index

    def flags(self, index):
        return Qt.ItemIsEnabled
        if not index.isValid():
            return Qt.ItemIsEnabled
        index = QModelIndex(index)  # explicitly convert from QPersistentModelIndex
        item = self.itemFromIndex(index)
        return item.flags(index)

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        index = QModelIndex(index)  # explicitly convert from QPersistentModelIndex

        #if role == Qt.EditRole:
            #item = self.itemFromIndex(index)
            #item.data_ = value
            #self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index, index)
            #return True

        if role == Qt.CheckStateRole:
            item = self.itemFromIndex(index)
            checked = (value.toInt()[0] == Qt.Checked)
            item.set_visible(checked)
            self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index, index)
            return True

        if role == Qt.EditRole:
            item = self.itemFromIndex(index)
            return item.setData(index, value, role)

        if role == DataRole:
            item = self.itemFromIndex(index)
            if item.setData(index, value, role):
                self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index, index.sibling(index.row(), 1))
            return True

        return False

    def insertRows(self, position, rows=1, index=QModelIndex()):
        index = QModelIndex(index)  # explicitly convert from QPersistentModelIndex
        item = self.itemFromIndex(index)
        if isinstance(item, RootAnnotationModelItem):
            self.beginInsertRows(QModelIndex(), position, position + rows - 1)
            for row in range(rows):
                file = File('')
                item.data_.files.insert(position + row, file)
                item.children_.insert(position + row, FileAnnotationModelItem(file, item))
            self.endInsertRows()
            self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index, index)
            self.set_dirty(True)
            return True
        # TODO handle inserts of rects, points etc

    def removeRows(self, position, rows=1, index=QModelIndex()):
        index = QModelIndex(index)  # explicitly convert from QPersistentModelIndex
        item = self.itemFromIndex(index)
        self.beginRemoveRows(index, position, position + rows - 1)
        data_changed = item.removeRows(position, rows)
        self.endRemoveRows()
        if data_changed:
            self.set_dirty(True)
            return True
        return False

    def addAnnotation(self, frameidx, ann={}, **kwargs):
        ann.update(kwargs)
        print "addAnnotation", ann
        frameidx = QModelIndex(frameidx)  # explicitly convert from QPersistentModelIndex
        item = self.itemFromIndex(frameidx)
        assert isinstance(item, FrameModelItem)

        next = len(item.children())
        self.beginInsertRows(frameidx, next, next)
        item.addAnnotation(ann)
        self.endInsertRows()
        self.setDirty(True)

        return True

    def removeAnnotation(self, annidx):
        annidx = QModelIndex(annidx)  # explicitly convert from QPersistentModelIndex
        item = self.itemFromIndex(annidx)
        assert isinstance(item, AnnotationModelItem)

        parent = item.parent_
        parentidx = annidx.parent()
        assert isinstance(parent, FrameModelItem)

        pos = parent.rowOfChild(item)
        self.beginRemoveRows(parentidx, pos, pos)
        parent.removeAnnotation(pos)
        self.endRemoveRows()
        self.setDirty(True)

        return True

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0: return QVariant("File/Type")
            elif section == 1: return QVariant("Value")
        return QVariant()

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
        self.setSelectionBehavior(QTreeView.SelectItems)
        self.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.setSortingEnabled(True)

        self.connect(self, SIGNAL("expanded(QModelIndex)"), self.expanded)

    def resizeColumns(self):
        for column in range(self.model().columnCount(QModelIndex())):
            self.resizeColumnToContents(column)

    def expanded(self):
        self.resizeColumns()

    def setModel(self, model):
        QTreeView.setModel(self, model)
        self.resizeColumns()

    def keyPressEvent(self, event):
        ## handle deletions of items
        if event.key() == Qt.Key_Delete:
            index = self.currentIndex()
            if not index.isValid():
                return
            parent = self.model().parent(index)
            self.model().removeRow(index.row(), parent)

        ## it is important to use the keyPressEvent of QAbstractItemView, not QTreeView
        QAbstractItemView.keyPressEvent(self, event)

    def rowsInserted(self, index, start, end):
        QTreeView.rowsInserted(self, index, start, end)
        self.resizeColumns()
#        self.setCurrentIndex(index.child(end, 0))

    def selectionModel(self):
        return QAbstractItemView.selectionModel(self)

def someAnnotations():
    annotations = []
    annotations.append({'type': 'rect',
                        'x': '10',
                        'y': '20',
                        'w': '40',
                        'h': '60'})
    annotations.append({'type': 'rect',
                        'x': '80',
                        'y': '20',
                        'w': '40',
                        'h': '60'})
    annotations.append({'type': 'point',
                        'x': '30',
                        'y': '30'})
    annotations.append({'type': 'point',
                        'x': '100',
                        'y': '100'})
    return annotations

def defaultAnnotations():
    annotations = []
    import os, glob
    if os.path.exists('/cvhci/data/multimedia/bigbangtheory/still_images/s1e1/'):
        images = glob.glob('/cvhci/data/multimedia/bigbangtheory/still_images/s1e1/*.png')
        images.sort()
        for fname in images:
            file = {
                'filename': fname,
                'type': 'image',
                'annotations': someAnnotations()
            }
            annotations.append(file)

    for i in range(5):
        file = {
            'filename': 'file%d.png' % i,
            'type': 'image',
            'annotations': someAnnotations()
        }
        annotations.append(file)
    for i in range(5):
        file = {
            'filename': 'file%d.avi' % i,
            'type':     'video',
            'frames': [],
        }
        for j in range(5):
            frame = {
                'num':       '%d' % j,
                'timestamp': '123456.789',
                'annotations': someAnnotations()
            }
            file['frames'].append(frame)
        annotations.append(file)
    return annotations


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    annotations = defaultAnnotations()

    model = AnnotationModel(annotations)

    wnd = AnnotationTreeView()
    wnd.setModel(model)
    wnd.show()

    sys.exit(app.exec_())

