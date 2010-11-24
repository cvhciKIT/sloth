from PyQt4.QtGui import *
from PyQt4.Qt import *

class AnnotationGraphicsItem(QAbstractGraphicsShapeItem):
    def __init__(self,controls_enabled=True, parent=None, **kwargs):
        super(AnnotationGraphicsItem, self).__init__(parent)

        self.setFlags(QGraphicsItem.ItemIsSelectable|QGraphicsItem.ItemIsMovable)

        self.text_font_ = QFont()
        self.text_font_.setPointSize(4)
        self.text_item_ = QGraphicsSimpleTextItem()
        self.text_item_.setFont(self.text_font_)
        self.updateText()

    def boundingRect(self):
        return QRectF(0, 0, 0, 0)

    def updateText(self):
        self.text_item_.setText("CLASS")

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            self.setControlsVisible(value.toBool())
        return QGraphicsItem.itemChange(self, change, value)

    def setControlsVisible(self, visible=True):
        self.controls_visible_ = visible
        #for corner in self.corner_items_:
        #    corner.setVisible(self.controls_enabled_ and self.controls_visible_)


