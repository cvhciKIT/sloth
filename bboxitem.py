from items import ItemInserter, AnnotationGraphicsItem
from PyQt4.QtGui import *
from PyQt4.Qt import *

class BodyBoundingboxItemInserter(ItemInserter):
    def __init__(self, scene, mode=None):
        ItemInserter.__init__(self, scene, mode)
        self.point_items_ = []
        self.points_      = []

    def mousePressEvent(self, event, index):
        pos = event.scenePos()
        self.points_.append((pos.x(), pos.y()))
        item = QGraphicsEllipseItem(pos.x()-2, pos.y()-2, 4, 4)
        item.setPen(Qt.red)
        self.point_items_.append(item)
        self.scene().addItem(item)

        event.accept()
        if self.complete(index):
            self.clear()

    def complete(self, index):
        if len(self.points_) == 4:
            ann = {'type': 'bodybbox',
                   'x1': self.points_[0][0], 'y1': self.points_[0][1],
                   'x2': self.points_[1][0], 'y2': self.points_[1][1],
                   'x3': self.points_[2][0], 'y3': self.points_[2][1],
                   'x4': self.points_[3][0], 'y4': self.points_[3][1]}
            index.model().addAnnotation(index, ann)
            return True
        return False

    def clear(self):
        for item in self.point_items_:
            self.scene().removeItem(item)
        self.point_items_ = []
        self.points_      = []

class BodyBoundingboxItem(AnnotationGraphicsItem):
    def __init__(self, index, parent=None):
        AnnotationGraphicsItem.__init__(self, index, parent)

        self.data_   = self.index().data(DataRole).toPyObject()
        self.points_ = [(self.data_['x1'], self.data_['y1']),
                        (self.data_['x2'], self.data_['y2']),
                        (self.data_['x3'], self.data_['y3']),
                        (self.data_['x4'], self.data_['y4'])]

    def boundingRect(self):
        return QRectF(QPointF(0, 0), QSizeF(20, 20))

    def paint(self, painter, option, widget = None):
        pen = self.pen()
        if self.isSelected():
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())

