import sys, os
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class ControlButtonWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop)
        self.back_button = QPushButton("<")
        self.forward_button = QPushButton(">")
        self.label_ = QLabel("<center><b></b></center>")
        layout.addWidget(self.back_button)
        layout.addWidget(self.label_)
        layout.addWidget(self.forward_button)
        self.setLayout(layout)

    def setFrameNumAndTimestamp(self, num, timestamp):
        self.label_.setText("<center><b>%d / %f</b></center>" % (num, timestamp))

    def setFilename(self, filename):
        self.label_.setText("<center><b>%s</b></center>" % (filename, ))
