from PyQt4.QtCore import Qt, QRect, QSize, QPoint
from PyQt4.QtGui  import QLayout, QSizePolicy, QWidgetItem


class FloatingLayout(QLayout):
    def __init__(self, parent=None):
        QLayout.__init__(self, parent)
        self._items = []
        self._updateMinimumSize()

    def _updateMinimumSize(self, height=None):
        w, h = 0, 0
        for item in self._items:
            w = max(w, item.minimumSize().width())
            h = max(h, item.minimumSize().height())

        left, top, right, bottom = self.getContentsMargins()
        w += left + right
        h += top + bottom

        if height is None:
            current_width = self.contentsRect().width()
            if current_width > 0:
                height = self.heightForWidth(current_width + left + right)
        if height is not None:
            h = max(h, height)

        self._min_w, self._min_h = w, h

    def _layoutChildren(self, rect, appl=True):
        left, top, right, bottom = self.getContentsMargins()
        r = rect.adjusted(+left, +top, -right, -bottom)
        x, y = r.x(), r.y()
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

        return y + lineHeight - r.y() + top + bottom

    def heightForWidth(self, width):
        return self._layoutChildren(QRect(0, 0, width, 0), False)

    def setGeometry(self, r):
        QLayout.setGeometry(self, r)
        new_height = self._layoutChildren(r)
        if new_height != self._min_h:
            self._updateMinimumSize(new_height)
            i = 0
            wid = self.parentWidget()
            while wid is not None:
                wid.updateGeometry()
                wid = wid.parentWidget()
                i += 1

    def insertItem(self, pos, item):
        self._items.insert(pos, item)
        self.invalidate()

    def insertWidget(self, pos, wid):
        self.addChildWidget(wid)
        self.insertItem(pos, QWidgetItem(wid))

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def hasHeightForWidth(self):
        return True

    def itemAt(self, index):
        if index < 0 or index >= len(self._items):
            return None
        return self._items[index]

    def minimumSize(self):
        return QSize(self._min_w, self._min_h)

    def takeAt(self, index):
        if index < 0 or index >= len(self._items):
            return None
        else:
            item = self._items[index]
            del self._items[index]
            return item

    def sizeHint(self):
        return self.minimumSize()

