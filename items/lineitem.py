from PyQt4.QtGui import *
from PyQt4.Qt import *
from annotationitem import *

class LineItem(AnnotationGraphicsItem):

    def __init__(self, pos, endPoint, parent=None):
        AnnotationGraphicsItem.__init__(self, False, parent)
        self.setPos(pos)
        self.endPoint_ = endPoint
        self.setFlags(QGraphicsItem.ItemIsSelectable|QGraphicsItem.ItemIsMovable)
        self.setPen(QColor('green'))

    def resizeContents(self, rect):
        pass

    def boundingRect(self):
        width = abs(self.endPoint_.x() - self.pos().x())
        height = abs(self.endPoint_.y() - self.pos().y())
        return QRectF(-10, -10, width, height)

    def paint(self, painter, option, widget = None):
        pen = self.pen()
        if self.isSelected():
            pen.setColor(QColor('red'))
        painter.setPen(pen)
        painter.drawLine(self.pos, self.endPoint_)

    def itemChange(self, change, value):
        return AnnotationGraphicsItem.itemChange(self, change, value)
    


