from PyQt4.QtGui import *
from PyQt4.QtCore import *

class FloatingLayout(QLayout):
    def __init__(self, parent=None):
        QLayout.__init__(self, parent)
        self._items = []

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if index < 0 or index >= len(self._items):
            return None
        return self._items[index]

    def takeAt(self, index):
        if index < 0 or index >= len(self._items):
            return None
        else:
            item = self._items[index]
            del self._items[index]
            return item

    def sizeHint(self):
        return self.minimumSize()

    def setGeometry(self, r):
        QLayout.setGeometry(self, r)
        self.layoutChildren(r)

    def minimumSize(self):
        sz = QSize(0, 20)
        for item in self._items:
            sz.rwidth = max(sz.width(), item.minimumSize().width())
        return sz

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.layoutChildren(QRect(0, 0, width, 100), False)
        return height

    def layoutChildren(self, r, appl=True):
        line_width  = r.x()
        line_height = 0
        line_top    = r.y()
        max_width   = r.x() + r.width()

        for item in self._items:
            sz_hint = item.sizeHint()
            if line_width != r.x() and line_width + sz_hint.width() > max_width:
                # start new line
                line_top += line_height
                line_width = r.x()
                line_height = 0
            if appl:
                item.setGeometry(QRect(QPoint(line_width, line_top), sz_hint))

            line_width += sz_hint.width()
            line_height = max(line_height, sz_hint.height())

        return line_top + line_height
