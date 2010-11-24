#!/usr/bin/python
import sys, os
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class MainWindow(QMainWindow):
    def __init__(self, argv, parent=None):
        QMainWindow.__init__(self, parent)

        vlayout = QVBoxLayout()
        for i in range(5):
            button = QPushButton("TestButton %d" % i)
            button.clicked.connect(self.clickedButton)
            vlayout.addWidget(button)

        hlayout = QHBoxLayout()
        self.redlabel = QLabel("mainlabel")
        self.redlabel.setStyleSheet("QLabel {background-color: red}")
        hlayout.addLayout(vlayout)
        hlayout.addWidget(self.redlabel, 1)

        central = QWidget()
        central.setLayout(hlayout)
        self.setCentralWidget(central)

    def clickedButton(self):
        button = self.sender()
        print button.text()
        self.redlabel.setText(button.text())

def main():
    app = QApplication(sys.argv)

    wnd = MainWindow(sys.argv[1:])
    wnd.show()

    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())

