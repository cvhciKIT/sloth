#!/usr/bin/python
import sys, os, math
from PyQt4.QtCore import *
from PyQt4.QtGui  import *

class GraphicsView(QGraphicsView):
    # Signals
    scaleChanged = pyqtSignal(float)
    focusIn      = pyqtSignal()

    def __init__(self, parent=None):
        QGraphicsView.__init__(self, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setFrameStyle(QFrame.NoFrame)

        self.current_scale_ = 1
        self.active_ = False

    def isActive(self):
        return self.active_

    def activate(self):
        if not self.active_:
            self.active_ = True
            self.setFocus(Qt.OtherFocusReason)
            self.setFrameStyle(QFrame.Panel)
            self.update()

    def deactivate(self):
        if self.active_:
            self.active_ = False
            self.clearFocus()
            self.setFrameStyle(QFrame.NoFrame)
            self.update()

    def setScaleRelative(self, factor):
        QGraphicsView.scale(self, factor, factor)
        self.current_scale_ *= factor
        self.scaleChanged.emit(self.current_scale_)
        # TODO: Stop at minimum scale

    def setScaleAbsolute(self, scale):
        m = QMatrix()
        m.scale(scale, scale)
        self.current_scale_ = scale
        self.setMatrix(m)
        self.scaleChanged.emit(self.current_scale_)
        # TODO: Stop at minimum scale

    def getScale(self):
        return self.current_scale_

    def wheelEvent(self, event):
        factor = 1.41 ** (event.delta() / 240.0)
        self.setScaleRelative(factor)

    def focusInEvent(self, event):
        self.focusIn.emit()

    # TODO: Make window panable by CTRL-Mouse-Drag or similar

class FrameViewer(QWidget):
    # Signals
    activeSceneViewChanged = pyqtSignal(GraphicsView)

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)

    def getActiveSceneView(self):
        pass

    def activateNextSceneView(self):
        pass

    def activatePreviousSceneView(self):
        pass

    def setActiveScaleAbsolute(self, scale):
        self.getActiveSceneView().setScaleAbsolute(scale)

    def setActiveScaleRelative(self, scale):
        self.getActiveSceneView().setScaleRelative(scale)

class SingleFrameViewer(FrameViewer):
    def __init__(self, annotation_scene, parent=None):
        FrameViewer.__init__(self, parent)
        self.scene = annotation_scene
        self.scene_view = GraphicsView()
        self.scene_view.setScene(self.scene)
        self.scene_view.activate()
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.scene_view)
        self.setLayout(self.layout)

    def getActiveSceneView(self):
        return self.scene_view

class MultiFrameEqualViewer(FrameViewer):
    def __init__(self, annotation_scenes, parent=None):
        assert(len(annotation_scenes) > 0)
        FrameViewer.__init__(self, parent)
        self.active_scene_view = -1
        self.scenes = annotation_scenes
        self.scene_views = []
        for scene in self.scenes:
            scene_view = GraphicsView()
            scene_view.setScene(scene)
            scene_view.focusIn.connect(self.activateFocusedSceneView)
            self.scene_views.append(scene_view)
        n_rows = math.ceil(math.sqrt(len(self.scene_views)))
        n_cols = math.ceil(len(self.scenes) / n_rows)
        self.layout = QGridLayout(self)
        for i, scene_view in enumerate(self.scene_views):
            self.layout.addWidget(scene_view, i/n_cols, i%n_cols)
        self.setLayout(self.layout)
        self.activateSceneView(0)

    def activateSceneView(self, index):
        if index != self.active_scene_view:
            for scene_view in self.scene_views:
                scene_view.deactivate()
            self.active_scene_view = index
            self.scene_views[index].activate()
            self.activeSceneViewChanged.emit(self.getActiveSceneView())

    def activateFocusedSceneView(self):
        sender = self.sender()
        for index, scene_view in enumerate(self.scene_views):
            if scene_view == sender:
                self.activateSceneView(index)

    def getActiveSceneView(self):
        return self.scene_views[self.active_scene_view]

def get_dummy_scene(filename):
    scene = QGraphicsScene()
    scene.addPixmap(QPixmap(filename))
    return scene

def main():
    app = QApplication(sys.argv)

    scenes = []
    for i in range(4):
        scenes.append(get_dummy_scene("/home/mfischer/data/test.jpg"))

    #viewer = SingleFrameViewer(scene)
    viewer = MultiFrameEqualViewer(scenes)
    viewer.show()

    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())

# Necessary information
# - Functionalities
#   - Display zoom level
