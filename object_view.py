#!/usr/bin/python
import sys, os
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from annotationscene import *
from annotationmodel import *

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
        buttonRectangle = QPushButton("Rectangle")
        buttonRectangle.clicked.connect(self.clickedRectangle)
        vlayout.addWidget(buttonRectangle)
        buttonPolygon = QPushButton("Polygon")
        buttonPolygon.clicked.connect(self.clickedPolygon)
        vlayout.addWidget(buttonPolygon)


        hlayout = QHBoxLayout()
        self.view_ = QGraphicsView()        
        self.annotree_ = AnnotationTreeView()
        hlayout.addLayout(vlayout)
        hlayout.addWidget(self.view_, 1)
        hlayout.addWidget(self.annotree_)
        
        self.scene_ = AnnotationScene(self)
        self.view_.setScene(self.scene_)

        central = QWidget()
        central.setLayout(hlayout)
        self.setCentralWidget(central)

    def setModel(self, model):
        self.annotree_.setModel(model)
        self.scene_.setModel(model)

        file_index = model.index(0, 0, QModelIndex())
        frame_index = model.index(0, 0, file_index)
        self.scene_.setRoot(frame_index)

    def clickedSelect(self):
        self.scene_.setMode(None)

    def clickedPoint(self):
        self.scene_.setMode({'type': 'point'})

    def clickedRectangle(self):
        self.scene_.setMode({'type': 'rect'})

    def clickedPolygon(self):
        self.scene_.setMode({'type': 'polygon'})


def main():
    import sys
    app = QApplication(sys.argv)

    annotations = defaultAnnotations()
    model = AnnotationModel(annotations)

    wnd = MainWindow(sys.argv[1:])
    wnd.resize(800, 600)
    wnd.setModel(model)
    wnd.show()

    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())

