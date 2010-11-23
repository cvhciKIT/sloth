from PyQt4.QtGui import *
from PyQt4.QtCore import *
from functools import partial
import os.path

class ModelItem:
    def __init__(self, parent=None):
        self.parent_   = parent
        self.children_ = []

    def children(self):
        return self.children_

    def parent(self):
        return self.parent_

    def rowOfChild(self, item):
        for row, child in enumerate(self.children_):
            if child is item:
                return row
        return -1

    def data(self, index, role):
        return QVariant()

class RootModelItem(ModelItem):
    def __init__(self, files):
        ModelItem.__init__(self, None)
        self.files_ = files

        for file in files:
            fmi = FileModelItem(file, self)
            self.children_.append(fmi)

class FileModelItem(ModelItem):
    def __init__(self, file, parent):
        ModelItem.__init__(self, parent)
        self.file_ = file

        for frame in file['frames']:
            fmi = FrameModelItem(frame, self)
            self.children_.append(fmi)

    def filename(self):
        return self.file_['filename']

    def data(self, index, role):
        if role == Qt.DisplayRole and index.column() == 0:
            return self.filename()
        return QVariant()

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

    def data(self, index, role):
        if role == Qt.DisplayRole and index.column() == 0:
            return "%d / %.3f" % (self.framenum(), self.timestamp())
        return QVariant()

class AnnotationModelItem(ModelItem):
    def __init__(self, annotations, parent):
        ModelItem.__init__(self, parent)
        self.annotations_ = annotations

        for key, value in annotations.iteritems():
            self.children_.append(KeyValueModelItem(key, value, self))

    def type(self):
        return self.annotations_['type']

    def data(self, index, role):
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return self.type()
            else:
                return QVariant()

class KeyValueModelItem(ModelItem):
    def __init__(self, key, value, parent):
        ModelItem.__init__(self, parent)
        self.key_   = key
        self.value_ = value

    def data(self, index, role):
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return self.key_
            elif index.column() == 1:
                return self.value_
            else:
                return QVariant()


class AnnotationModelItemOld(object):
    def __init__(self, data, model, parent=None):
        self.children_ = []
        self.type_ = type
        self.data_ = data
        self.parent_ = parent
        self.model_ = model
        self.visible_ = True

    def parent(self):
        return self.parent_

    def model(self):
        return self.model_

    def children(self):
        return self.children_

    def rowOfChild(self, item):
        for row, child in enumerate(self.children_):
            if child is item:
                return row
        return -1

    def data(self, index, role):
        return QVariant()

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def removeRows(self, position, rows):
        return False

    def visible(self): return self.visible_
    def set_visible(self, visible): self.visible_ = visible

    def isCheckable(self, column): return False

class PropertyDelegate(QItemDelegate):
     def __init__(self, model, parent=None):
         super(PropertyDelegate, self).__init__(parent)
         self.model_ = model

     def createEditor(self, parent, option, index):
         if index.column() == 0:
             return None
         item = self.model_.itemFromIndex(index)
         return item.createEditor(parent, option, index)

     def setEditorData(self, editor, index):
         item = self.model.getItem(index)
         item.setEditorData(editor, index)

     def setModelData(self, editor, model, index):
         item = self.model.getItem(index)
         item.setModelData(editor, model, index)

#    def updateEditorGeometry(self, editor, option, index):
#        editor.setGeometry(option.rect)

     def paint(self, painter, option, index):
         item = self.model.getItem(index)
         if isinstance(item, ColorProperty) and index.column() == 1:
             item.paint(painter, option, index)
             return
         QtGui.QItemDelegate.paint(self, painter, option, index)

class Property(AnnotationModelItem):
    def __init__(self, key, data, model, parent=None):
        super(Property, self).__init__(data, model, parent)
        self.key_ = key
         
    def data(self, index, role):
        if index.column() == 0:
            return QVariant(self.key_)
        elif index.column() == 1:
            return QVariant(str(self.data_[self.key_]))
        return QVariant("")

    def flags(self, index):
        if index.column() == 1:
            return super(Property, self).flags(index) | Qt.ItemIsEditable
        return super(Property, self).flags(index)

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            return self.parent().setData(index, value, role)
        return False

    def createEditor(self, parent, option, index):
        return None

    def setEditorData(self, editor, index):
        return

    def setModelData(self, editor, model, index):
        return

class StringProperty(Property):
     def __init__(self, key, data, model, parent):
         super(StringProperty, self).__init__(key, data, model, parent)

     def createEditor(self, parent, option, index):
         editor = QLineEdit(parent)
         return editor

     def setEditorData(self, editor, index):
         editor.setText(str(self.data_[self.key_]))

     def setModelData(self, editor, model, index):
         self.data_[self.key_] = str(editor.text())

class RootAnnotationModelItem(AnnotationModelItem):
    def __init__(self, data, model):
        super(RootAnnotationModelItem, self).__init__(data, model)
        for row, file in enumerate(self.data_.files):
            self.children_.append(FileAnnotationModelItem(file, model, self))

    def removeRows(self, position, rows):
        self.data_.files = self.data_.files[:position] + self.data_.files[position+rows:]
        self.children_ =  self.children_[:position] + self.children_[position+rows:]
        return True

class FileAnnotationModelItem(AnnotationModelItem):
    def __init__(self, data, model, parent):
        super(FileAnnotationModelItem, self).__init__(data, model, parent)
        for row, annotation in enumerate(self.data_.annotations):
            if annotation.type == 'rect':
                self.children_.append(RectAnnotationModelItem(annotation, model, self))
            elif annotation.type == 'mask':
                self.children_.append(MaskAnnotationModelItem(annotation, model, self))
            elif annotation.type == 'point':
                self.children_.append(PointAnnotationModelItem(annotation, model, self))

    def data(self, index, role):
        if role == DataRole:
            return QVariant(self.data_.filename)

        if index.column() == 0:
            return QVariant(os.path.split(self.data_.filename)[1])
        else:
            return QVariant("")

    def removeRows(self, position, rows):
        self.data_.annotations = self.data_.annotations[:position] + self.data_.annotations[position+rows:]
        self.children_ =  self.children_[:position] + self.children_[position+rows:]
        return True

class RectAnnotationModelItem(AnnotationModelItem):
    def __init__(self, data, model, parent):
        super(RectAnnotationModelItem, self).__init__(data, model, parent)
        self.children_.append(StringProperty('id', data, model, self))
        self.children_.append(StringProperty('class', data, model, self))
        self.children_.append(StringProperty('x', data, model, self))
        self.children_.append(StringProperty('y', data, model, self))
        self.children_.append(StringProperty('width', data, model, self))
        self.children_.append(StringProperty('height', data, model, self))

    def data(self, index, role):
        if role == GraphicsItemRole:
            return QVariant(AnnotationGraphicsRectItem(self, index))
        elif role == DataRole:
            return QVariant(QRectF(self.data_.x, self.data_.y, self.data_.width, self.data_.height))
        elif role == Qt.DisplayRole:
            if index.column() == 0:
                return QVariant("Rect")
            elif index.column() == 1:
                s = "id: '%s', class: '%s', (%d, %d, %d, %d)" % \
                        (self.data_['id'], self.data_['class'], int(self.data_['x']), int(self.data_['y']),
                         int(self.data_['width']), int(self.data_['height']))
                return QVariant(s)
        assert False

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            assert index.model().itemFromIndex(index.parent()) == self
            check_pairs = [('id', value.toString), ('class', value.toString),
                    ('x', value.toString), ('y', value.toString),
                    ('height', value.toString), ('width', value.toString)]
            key, f = check_pairs[index.row()]
            if self.data_[key] != f():
                self.data_[key] = str(f())
                index.model().emit(SIGNAL('dataChanged(QModelIndex,QModelIndex)'), index.parent(), index.parent())
                index.model().emit(SIGNAL('dataChanged(QModelIndex,QModelIndex)'), index, index)
                return True
            return False

        if role == DataRole:
            rect = value.toRectF().toRect()
            modified = False
            check_pairs = [('x', rect.topLeft().x), ('y', rect.topLeft().y),
                ('width', rect.size().width), ('height', rect.size().height)]
            for key, f in check_pairs:
                if self.data_[key] != f():
                    self.data_[key] = f()
                    modified = True

            return modified
        return False

    def flags(self, index):
        if index.column() == 0:
            return Qt.ItemIsUserCheckable | super(RectAnnotationModelItem, self).flags(index)
        return super(RectAnnotationModelItem, self).flags(index)

    def isCheckable(self, column):
        if column == 0:
            return True
        return False

class MaskAnnotationModelItem(AnnotationModelItem):
    def __init__(self, data, model, parent):
        super(MaskAnnotationModelItem, self).__init__(data, model, parent)
        self.children_.append(StringProperty('id', data, model, self))
        self.children_.append(StringProperty('class', data, model, self))
        self.children_.append(StringProperty('filename', data, model, self))
        self.image_ = None
        self.shape_ = None
        self.dirty_ = False

    def set_dirty(self, dirty=True): self.dirty_ = dirty
    def dirty(self): return self.dirty_

    def data(self, index, role):
        if role == GraphicsItemRole:
            return QVariant(AnnotationGraphicsMaskItem(self, index))
        elif role == DataRole:
            return QVariant(self.image())
        elif role == Qt.DisplayRole:
            if index.column() == 0:
                return QVariant("Mask")
            elif index.column() == 1:
                s = "id: '%s', class: '%s'" % (self.data_['id'], self.data_['class'])
                return QVariant(s)

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            assert index.model().itemFromIndex(index.parent()) == self
            check_pairs = [('id', value.toString), ('class', value.toString)]
            key, f = check_pairs[index.row()]
            if self.data_[key] != f():
                self.data_[key] = str(f())
                index.model().emit(SIGNAL('dataChanged(QModelIndex,QModelIndex)'), index.parent(), index.parent())
                index.model().emit(SIGNAL('dataChanged(QModelIndex,QModelIndex)'), index, index)
                return True
            return False

        if role == DataRole:
            assert value.type() == QVariant.Image
            self.image_ = QImage(value)
            self.set_dirty()
            index.model().emit(SIGNAL('dataChanged(QModelIndex,QModelIndex)'), index, index)
            # emit dataChanged (?) shouldn't be necessary
            return True
        return False

    def flags(self, index):
        if index.column() == 0:
            return Qt.ItemIsUserCheckable | super(MaskAnnotationModelItem, self).flags(index)
        return super(MaskAnnotationModelItem, self).flags(index)

    def isCheckable(self, column):
        if column == 0:
            return True
        return False

    def filename(self):
        if os.path.isabs(self.data_.filename):
            return self.data_.filename
        else:
            return os.path.join(self.model().baseDir(), self.data_.filename)

    def image(self):
        if self.image_ is None:
            if os.path.exists(self.filename()):
                self.image_ = QImage(self.filename()).convertToFormat(QImage.Format_MonoLSB)
            else:
                # find parent image
                parent = self.parent()
                while (parent is not None):
                    if isinstance(parent, FileAnnotationModelItem):
                        break
                if parent is None:
                    print >>sys.stderr, "Error: mask annotation item does not have a File parent"
                else:
                    print 'Creating new mask for', self.filename()
                    im = QImage(parent.data_.filename)
                    self.image_ = QImage(im.width(), im.height(), QImage.Format_MonoLSB)
                    self.image_.fill(0)
                    self.set_dirty()

            # strange qt convention:
            # white == Qt.color0 == 0 is background
            # black == Qt.color1 == 1 is foreground
            # thus we switch the pixel values and reassign the colors
            self.image_.invertPixels()
        return self.image_

    def writeback(self):
        assert self.filename() is not None
        if not self.dirty(): return
        tmpimage = QImage(self.image())  # important to wrap this in a QImage constructor, otherwise no real copy made
        tmpimage.invertPixels()
        tmpimage.save(self.filename(), os.path.splitext(self.filename())[1][1:])

class PointAnnotationModelItem(AnnotationModelItem):
    def __init__(self, data, model, parent):
        super(PointAnnotationModelItem, self).__init__(data, model, parent)
        self.children_.append(StringProperty('id', data, model, self))
        self.children_.append(StringProperty('class', data, model, self))
        self.children_.append(StringProperty('x', data, model, self))
        self.children_.append(StringProperty('y', data, model, self))

    def data(self, index, role):
        if role == GraphicsItemRole:
            return QVariant(AnnotationGraphicsPointItem(self, index))
        elif role == DataRole:
            return QVariant(QPointF(self.data_.x, self.data_.y))
        elif role == Qt.DisplayRole:
            if index.column() == 0:
                return QVariant("Point")
            elif index.column() == 1:
                s = "id: '%s', class: '%s', (%d, %d)" % \
                        (self.data_['id'], self.data_['class'], int(self.data_['x']), int(self.data_['y']))
                return QVariant(s)
        return QVariant()

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            assert index.model().itemFromIndex(index.parent()) == self
            check_pairs = [('id', value.toString), ('class', value.toString),
                    ('x', value.toString), ('y', value.toString)]
            key, f = check_pairs[index.row()]
            if self.data_[key] != f():
                self.data_[key] = str(f())
                index.model().emit(SIGNAL('dataChanged(QModelIndex,QModelIndex)'), index.parent(), index.parent())
                index.model().emit(SIGNAL('dataChanged(QModelIndex,QModelIndex)'), index, index)
                return True
            return False

        if role == DataRole:
            point = value.toPointF().toPoint()
            modified = False
            check_pairs = [('x', point.x), ('y', point.y)]
            for key, f in check_pairs:
                if self.data_[key] != f():
                    self.data_[key] = f()
                    modified = True
            return modified

        return False

    def flags(self, index):
        if index.column() == 0:
            return Qt.ItemIsUserCheckable | super(PointAnnotationModelItem, self).flags(index)
        return super(PointAnnotationModelItem, self).flags(index)

    def isCheckable(self, column):
        if column == 0:
            return True
        return False

class AnnotationModel(QAbstractItemModel):
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
            self.emit(SIGNAL("dirtyChanged()"))

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

    def fileIndex(self, index):
        """return index that points to the (maybe parental) file object"""
        if not index.isValid():
            return QModelIndex()
        index = QModelIndex(index)  # explicitly convert from QPersistentModelIndex
        item = self.itemFromIndex(index)
        if isinstance(item, FileAnnotationModelItem):
            return index
        return self.fileIndex(index.parent())

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

        if event.key() == ord('A'):
            index = self.currentIndex()
            if not index.isValid():
                return
            self.model().addAnnotation(index,
                    {'type':'beer', 'alc': '5.1', 'name': 'rothaus'})

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
    return annotations

def defaultAnnotations():
    annotations = []
    for i in range(5):
        file = {
            'filename': 'file%d.png' % i,
            'type': 'image',
            'frames': []
        }
        file['frames'].append({'annotations': someAnnotations()})
        annotations.append(file)
    for i in range(5):
        file = {
            'filename': 'file%d.png' % i,
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

