#!/usr/bin/python
import sys, os
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from annotationscene import *

class MainWindow(QMainWindow):
    def __init__(self, argv, parent=None):
        QMainWindow.__init__(self, parent)

        vlayout = QVBoxLayout()
        buttonSelect = QPushButton("Select")
        buttonSelect.clicked.connect(self.clickedSelect)
        vlayout.addWidget(buttonSelect)
        buttonPoint = QPushButton("Point")
        buttonPoint.clicked.connect(self.clickedPoint)
        vlayout.addWidget(buttonPoint)
        buttonLine = QPushButton("Line")
        buttonLine.clicked.connect(self.clickedLine)
        vlayout.addWidget(buttonLine)
        buttonRectangle = QPushButton("Rectangle")
        buttonRectangle.clicked.connect(self.clickedRectangle)
        vlayout.addWidget(buttonRectangle)
        buttonPolygon = QPushButton("Polygon")
        buttonPolygon.clicked.connect(self.clickedPolygon)
        vlayout.addWidget(buttonPolygon)


        hlayout = QHBoxLayout()
        self.view_ = QGraphicsView()        
        hlayout.addLayout(vlayout)
        hlayout.addWidget(self.view_, 1)

        self.scene_ = AnnotationScene(self)
        self.view_.setScene(self.scene_)

        central = QWidget()
        central.setLayout(hlayout)
        self.setCentralWidget(central)

    def clickedSelect(self):
        self.scene_.setMode(None)

    def clickedPoint(self):
            self.scene_.setMode({'type': 'point'})

    def clickedRectangle(self):
        self.scene_.setMode({'type': 'rect'})

    def clickedLine(self):
        self.scene_.setMode(LINE)

    def clickedPolygon(self):
        self.scene_.setMode({'type': 'polygon'})


def main():
    app = QApplication(sys.argv)

    wnd = MainWindow(sys.argv[1:])
    wnd.resize(800,600)
    wnd.show()

    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())

