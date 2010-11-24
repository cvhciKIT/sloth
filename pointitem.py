from PyQt4.QtGui import *
from PyQt4.Qt import *
from annotationitem import *

class AnnotationGraphicsPointItem(AnnotationGraphicsItem):
    size_ = 4

    def __init__(self, pos, parent=None):
        AnnotationGraphicsItem.__init__(self, False, parent)
        self.setPos(pos)
        self.setFlags(QGraphicsItem.ItemIsSelectable|QGraphicsItem.ItemIsMovable)
        self.setPen(QColor('green'))

    def resizeContents(self, rect):
        pass

    def boundingRect(self):
        return QRectF(-2*self.size_,
                       -2*self.size_,
                       4*self.size_,
                       4*self.size_)

    def paint(self, painter, option, widget = None):
        pen = self.pen()
        if self.isSelected():
            pen.setColor(QColor('red'))
        painter.setPen(pen)
        painter.drawEllipse(0,0,self.size_,self.size_)

    def itemChange(self, change, value):
        return AnnotationGraphicsItem.itemChange(self, change, value)
    


