from PyQt4.QtGui import *
from PyQt4.QtCore import *


class Label(QLabel):
    
    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)
        
    def mouseReleaseEvent(self, ev):
        menu = QMenu(self)
        menu.addActions(self.actions())
        menu.exec_(ev.globalPos())


class ControlButtonWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop)
        self.back_button = QPushButton("<")
        self.forward_button = QPushButton(">")
        self._label = Label("<center><b></b></center>")
        self._action_copy = QAction("Copy", self._label)
        self._label.addAction(self._action_copy)
        self._action_copy.triggered.connect(self.copyFilename)

        layout.addWidget(self.back_button)
        layout.addWidget(self._label)
        layout.addWidget(self.forward_button)
        self.setLayout(layout)

    def setFrameNumAndTimestamp(self, num, timestamp):
        self._label.setText("<center><b>%d / %f</b></center>" % (num, timestamp))

    def setFilename(self, filename):
        self._label.setText("<center><b>%s</b></center>" % (filename, ))

    @pyqtSlot()
    def copyFilename(self):
        doc = QTextDocument()
        doc.setHtml(self._label.text())
        text = doc.toPlainText()
        QApplication.clipboard().setText(text)
        QApplication.clipboard().setText(text, QClipboard.Selection)
