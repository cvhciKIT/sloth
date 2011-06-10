"""
The annotationmodel module contains the classes for the AnnotationModel.
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from functools import partial
import os.path
import okapy
import okapy.videoio as okv

TypeRole, DataRole, ImageRole = [Qt.UserRole + i + 1 for i in range(3)]

class ModelItem:
    def __init__(self):
        self.children_ = []
        self._pindex   = None
        self.model_    = None
        self.parent_   = None

    def children(self):
        return self.children_

    def model(self):
        return self.model_

    def parent(self):
        return self.parent_

    def rowOfChild(self, item):
        try:
            return self.children_.index(item)
        except:
            return -1

    def data(self, role=Qt.DisplayRole, column=0):
        return QVariant()

    def setParent(self, parent):
        assert self.parent_ is None
        self.parent_ = parent

    def setIndex(self, index):
        assert self._pindex is None
        self._pindex = QPersistentModelIndex(index)
        if index.isValid():
            self.model_ = index.model()

    def pindex(self):
        assert self._pindex is not None
        return self._pindex

    def index(self):
        assert self._pindex is not None
        return QModelIndex(self._pindex)

    def parentIndex(self):
        if self.parent_ is not None:
            return self.parent_.index()
        else:
            return QModelIndex()

    def appendChild(self, item):
        next_row = len(self.children_)
        index = self.index()
        self.model_.beginInsertRows(index, next_row, next_row)
        self.children_.append(item)
        item.setParent(self)
        self.model_.endInsertRows()
        item.setIndex(self.model_.index(next_row, 0, index))

    def deleteAllChildren(self):
        for child in self.children_:
            child.deleteAllChildren()

        self.model_.beginRemoveRows(self.index(), 0, len(self.children_) - 1)
        self.children_ = []
        self.model_.endRemoveRows()

    def deleteChild(self, arg):
        if arg isinstance ModelItem:
            self.deleteChild(self.children_.index(item))
        else:
            if pos < 0 or pos >= len(self.children_):
                raise IndexError("child index out of range")
            self.children_[pos].deleteAllChildren()
            self.model_.beginRemoveRows(self.index(), pos, pos)
            del self.children_[pos]
            self.model_.endRemoveRows()

class RootModelItem(ModelItem):
    def __init__(self, model, fileinfos):
        ModelItem.__init__(self)
        self.model_ = model
        self.setIndex(QModelIndex())

        for fileinfo in fileinfos:
            appendFileItem(fileinfo)

    def appendFileItem(self, fileinfo):
        item = FileModelItem.create(fileinfo, self)
        self.appendChild(item)

class FileModelItem(ModelItem):
    def __init__(self, fileinfo):
        ModelItem.__init__(self)
        self._fileinfo = fileinfo

    def filename(self):
        return self._fileinfo['filename']

    def data(self, role=Qt.DisplayRole, column=0):
        if role == Qt.DisplayRole and index.column() == 0:
            return os.path.basename(self.filename())
        return ModelItem.data(self, role, column)

    @staticmethod
    def create(fileinfo, parent):
        if fileinfo['type'] == 'image':
            return ImageFileModelItem(fileinfo, parent)
        elif fileinfo['type'] == 'video':
            return VideoFileModelItem(fileinfo, parent)

class ImageFileModelItem(FileModelItem):
    def __init__(self, fileinfo):
        FileModelItem.__init__(self, fileinfo)

        for ann in fileinfo['annotations']:
            item = AnnotationModelItem(ann)
            self.appendChild(item)

    def addAnnotation(self, ann):
        self.fileinfo_['annotations'].append(ann)
        item = AnnotationModelItem(ann)
        self.appendChild(item)

    # TODO
    def updateAnnotation(self, ann):
        child_found = False
        for child in self.children_:
            if child.type() == ann['type']:
                if (child.has_key('id') and ann.has_key('id') and child.value('id') == ann['id']) or (not child.has_key('id') and not ann.has_key('id')):
                    ann[None] = None
                    child.setData(index, QVariant(ann), DataRole)
                    child_found = True
                    break
        if not child_found:
            raise Exception("No ImageFileModelItem found that could be updated!")

    def removeAnnotation(self, pos):
        del self.fileinfo_['annotations'][pos]
        self.deleteChild(pos)

    def data(self, role=Qt.DisplayRole, column=0):
        elif role == DataRole:
            return self.fileinfo_
        return FileModelItem.data(self, role)

class VideoFileModelItem(FileModelItem):
    def __init__(self, fileinfo):
        FileModelItem.__init__(self, fileinfo)

        for frameinfo in fileinfo['frames']:
            item = FrameModelItem(frameinfo)
            self.appendChild(item)

class FrameModelItem(ModelItem):
    def __init__(self, frameinfo):
        ModelItem.__init__(self)
        self.frameinfo_ = frameinfo

        for ann in frameinfo['annotations']:
            item = AnnotationModelItem(ann)
            self.appendChild(item)

    def framenum(self):
        return int(self.frameinfo_.get('num', -1))

    def timestamp(self):
        return float(self.frameinfo_.get('timestamp', -1))

    def addAnnotation(self, ann):
        self.frameinfo_['annotations'].append(ann)
        item = AnnotationModelItem(ann)
        self.appendChild(item)

    # TODO
    def updateAnnotation(self, ann):
        child_found = False
        for child in self.children_:
            if child.type() == ann['type']:
                if (child.has_key('id') and ann.has_key('id') and child.value('id') == ann['id']) or (not child.has_key('id') and not ann.has_key('id')):
                    ann[None] = None
                    child.setData(index, QVariant(ann), DataRole)
                    child_found = True
                    break
        if not child_found:
            raise Exception("No FrameModelItem found that could be updated!")

    def removeAnnotation(self, pos):
        del self.frameinfo_['annotations'][pos]
        self.deleteChild(pos)

    def data(self, index, role=Qt.DisplayRole, column=0):
        if role == Qt.DisplayRole and index.column() == 0:
            return "%d / %.3f" % (self.framenum(), self.timestamp())
        return QVariant()

class AnnotationModelItem(ModelItem):
    def __init__(self, annotation):
        ModelItem.__init__(self)
        self.annotation_ = annotation
        # dummy key/value so that pyqt does not convert the dict
        # into a QVariantMap while communicating with the Views
        self.annotation_[None] = None

        for key, value in annotation.iteritems():
            if key == None:
                continue
            self.addChild(KeyValueModelItem(key))

    def type(self):
        return self.annotation_['type']

    def setData(self, index, data, role):
        if role == DataRole:
            print self.annotation_
            data = data.toPyObject()
            print data, type(data)
            print self.annotation_
            for key, value in data.iteritems():
                print key, value
                if not key in self.annotation_:
                    print "not in annotation: ", key
                    self.addChild(KeyValueModelItem(key))
                    self.annotation_[key] = data[key]

            for key in self.annotation_.keys():
                if not key in data:
                    # TODO
                    self.deleteChild(???)
                    del self.annotation_[key]
                else:
                    self.annotation_[key] = data[key]
                    # TODO: Emit data changed signal

            print "new annotation:", self.annotation_
            # TODO: Emit data changed signal
            return True
        return False

    def data(self, index, role=Qt.DisplayRole, column=0):
        if role == Qt.DisplayRole and column == 0:
            return self.type()
        elif role == TypeRole:
            return self.type()
        elif role == DataRole:
            return self.annotation_
        return QVariant()

    def setValue(self, key, value):
        self.annotation_[key] = value
        # TODO: Emit data changed signal

    def value(self, key):
        return self.annotation_[key]

    def has_key(self, key):
        return self.annotation_.has_key(key)

class KeyValueModelItem(ModelItem):
    def __init__(self, key):
        ModelItem.__init__(self)
        self._key = key

    def data(self, role=Qt.DisplayRole, column=0):
        if role == Qt.DisplayRole:
            if column == 0:
                return self._key
            elif column == 1:
                return self.parent().value(self._key)
            else:
                return QVariant()

class AnnotationModel(QAbstractItemModel):
    # signals
    dirtyChanged = pyqtSignal(bool, name='dirtyChanged')

    def __init__(self, annotations, parent=None):
        QAbstractItemModel.__init__(self, parent)
        self.annotations_ = annotations
        self.root_        = RootModelItem(self, self.annotations_)
        self.dirty_       = False
        self.basedir_     = ""

    def dirty(self):
        return self.dirty_

    def setDirty(self, dirty=True):
        previous = self.dirty_
        self.dirty_ = dirty
        if previous != dirty:
            self.dirtyChanged.emit(dirty)

    def basedir(self):
        return self.basedir_

    def setBasedir(self, dir):
        print "setBasedir: \"" + dir + "\"" 
        self.basedir_ = dir

    def itemFromIndex(self, index):
        index = QModelIndex(index)  # explicitly convert from QPersistentModelIndex
        if index.isValid():
            return index.internalPointer()
        return self.root_

    def index(self, row, column, parent_idx=QModelIndex()):
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

    def data(self, index, role=Qt.DisplayRole):
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

    def columnCount(self, index=QModelIndex()):
        return 2

    def rowCount(self, index=QModelIndex()):
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
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if not index.isValid():
            return Qt.ItemIsEnabled
        index = QModelIndex(index)  # explicitly convert from QPersistentModelIndex
        item = self.itemFromIndex(index)
        return item.flags(index)

    def setData(self, index, value, role=Qt.EditRole):
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
            print "setData", value.toPyObject()
            if item.setData(index, value, role):
                self.setDirty(True)
                # TODO check why this is needed (should be done by item.setData() anyway)
                self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index, index.sibling(index.row(), 1))
            return True

        return False

    def addAnnotation(self, imageidx, ann={}, **kwargs):
        ann.update(kwargs)
        print "addAnnotation", ann
        imageidx = QModelIndex(imageidx)  # explicitly convert from QPersistentModelIndex
        item = self.itemFromIndex(imageidx)
        assert isinstance(item, FrameModelItem) or isinstance(item, ImageFileModelItem)

        next = len(item.children())
        self.beginInsertRows(imageidx, next, next)
        item.addAnnotation(ann)
        self.endInsertRows()
        self.setDirty(True)

        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), imageidx, imageidx)

        return True

    def updateAnnotation(self, imageidx, ann={}, **kwargs):
        ann.update(kwargs)
        print "updateAnnotation", ann
        imageidx = QModelIndex(imageidx)  # explicitly convert from QPersistentModelIndex
        item = self.itemFromIndex(imageidx)
        assert isinstance(item, FrameModelItem) or isinstance(item, ImageFileModelItem)

        item.updateAnnotation(imageidx, ann)
        self.setDirty(True)

        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), imageidx, imageidx)

        return True

    def removeAnnotation(self, annidx):
        annidx = QModelIndex(annidx)  # explicitly convert from QPersistentModelIndex
        item = self.itemFromIndex(annidx)
        assert isinstance(item, AnnotationModelItem)

        parent = item.parent_
        parentidx = annidx.parent()
        assert isinstance(parent, FrameModelItem) or isinstance(parent, ImageFileModelItem)

        pos = parent.rowOfChild(item)
        self.beginRemoveRows(parentidx, pos, pos)
        parent.removeAnnotation(pos)
        self.endRemoveRows()
        self.setDirty(True)

        return True

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:   return QVariant("File/Type/Key")
            elif section == 1: return QVariant("Value")
        return QVariant()

    def getNextIndex(self, index):
        """returns index of next *image* or *frame*"""
        if not index.isValid():
            return QModelIndex()

        assert index == self.imageIndex(index)
        num_images = self.rowCount(index.parent())
        if index.row() < num_images - 1:
            return index.sibling(index.row()+1, 0)

        return index

    def getPreviousIndex(self, index):
        # TODO bool parameter to disable wrap around
        """returns index of previous *image* or *frame*"""
        if not index.isValid():
            return QModelIndex()

        assert index == self.imageIndex(index)
        if index.row() > 0:
            return index.sibling(index.row()-1, 0)

        return index

    def asDictList(self):
        """return annotations as python list of dictionary"""
        # TODO
        annotations = []
        if self.root_ is not None:
            for child in self.root_.children_:
                pass



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
#        self.setStyleSheet("""
#            QTreeView { selection-color: blue; show-decoration-selected: 1; }
#            QTreeView::item:alternate { background-color: #EEEEEE; }
#        """)

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

