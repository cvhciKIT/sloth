from PyQt4.QtCore import QSize
from PyQt4.QtGui import QVBoxLayout


# This is really really ugly, but the QDockWidget for some reason does not notice when
# its child widget becomes smaller...
# Therefore we manually set its minimum size when our own minimum size changes
class MyVBoxLayout(QVBoxLayout):
    def __init__(self, parent=None):
        QVBoxLayout.__init__(self, parent)
        self._last_size = QSize(0, 0)

    def setGeometry(self, r):
        QVBoxLayout.setGeometry(self, r)
        try:
            wid = self.parentWidget().parentWidget()

            new_size = self.minimumSize()
            if new_size == self._last_size: return
            self._last_size = new_size

            twid = wid.titleBarWidget()
            if twid is not None:
                theight = twid.sizeHint().height()
            else:
                theight = 0

            new_size += QSize(0, theight)
            wid.setMinimumSize(new_size)

        except Exception:
            pass
