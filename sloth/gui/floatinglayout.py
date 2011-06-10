from PyQt4.QtGui import *
from PyQt4.QtCore import *

class FloatingLayout(QLayout):
    def __init__(self, parent=None):
        QLayout.__init__(self, parent)
        self._items = []
        self._last_min_size = self.minimumSize()

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
        min_size = self.minimumSize()
        if self._last_min_size != min_size:
            self._last_min_size = min_size
            self.parentWidget().updateGeometry()

    def minimumSize(self):
        w = 0
        h = 0
        for item in self._items:
            w = max(w, item.minimumSize().width())
            h = max(h, item.minimumSize().height())

        left, top, right, bottom = self.getContentsMargins()
        current_width = self.contentsRect().width() - left - right
        if current_width > 0:
            h = self.heightForWidth(current_width)

        w += left + right
        h += top + bottom

        return QSize(w, h)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.layoutChildren(QRect(0, 0, width, 0), False)
        left, top, right, bottom = self.getContentsMargins()
        return height + top + bottom

    def layoutChildren(self, rect, appl=True):
        left, top, right, bottom = self.getContentsMargins()
        r = rect.adjusted(+left, +top, -right, -bottom)
        x = r.x();
        y = r.y();
        lineHeight = 0

        for item in self._items:
            wid = item.widget()
            spaceX = wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            spaceY = wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)

            sz_hint = item.sizeHint()
            if x != r.x() and x + sz_hint.width() >= r.right():
                # start new line
                x = r.x()
                y += lineHeight + spaceY
                lineHeight = 0
            if appl:
                item.setGeometry(QRect(QPoint(x, y), sz_hint))

            x += sz_hint.width() + spaceX
            lineHeight = max(lineHeight, sz_hint.height())

        return y + lineHeight - r.y()
