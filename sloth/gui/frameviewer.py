#!/usr/bin/python
import sys, os, math
import okapy
import okapy.videoio
import okapy.guiqt.utilities as ogu
from PyQt4.QtCore import *
from PyQt4.QtGui  import *

videos = []
scenes = []

class GraphicsView(QGraphicsView):
    # Signals
    scaleChanged = pyqtSignal(float)
    focusIn      = pyqtSignal()

    def __init__(self, parent=None):
        QGraphicsView.__init__(self, parent)
        #self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing);
        self.setStyleSheet("QFrame { border: 3px solid black }");
        self.active_ = False

    def setScene(self, scene):
        QGraphicsView.setScene(self, scene)
        #self.setScaleAbsolute(1)

    def getScale(self):
        if self.isTransformed():
            return self.transform().m11()
        else:
            return 1

    def isActive(self):
        return self.active_

    def activate(self):
        if not self.active_:
            self.active_ = True
            self.setFocus(Qt.OtherFocusReason)
            self.setStyleSheet("QFrame { border: 3px solid red }");
            self.update()

    def deactivate(self):
        if self.active_:
            self.active_ = False
            self.clearFocus()
            self.setStyleSheet("QFrame { border: 3px solid black }");
            self.update()

    def getMinScale(self):
        #min_scale_w = float(self.width()  - 2*self.frameWidth()) / (self.scene().width()+1)
        #min_scale_h = float(self.height() - 2*self.frameWidth()) / (self.scene().height()+1)
        #min_scale = min(min_scale_w, min_scale_h)
        return 0.1

    def getMaxScale(self):
        #max_scale_w = self.scene().height() / 5.0
        #max_scale_h = self.scene().width()  / 5.0
        #max_scale = min(max_scale_w, max_scale_h)
        #return max_scale
        return 20.0

    def setScaleAbsolute(self, scale):
        scale = max(scale, self.getMinScale())
        scale = min(scale, self.getMaxScale())
        self.setTransform(QTransform.fromScale(scale, scale))
        self.scaleChanged.emit(self.getScale())

    def setScaleRelative(self, factor):
        self.setScaleAbsolute(self.getScale() * factor)

    def wheelEvent(self, event):
        factor = 1.41 ** (event.delta() / 240.0)
        self.setScaleRelative(factor)

    def focusInEvent(self, event):
        self.focusIn.emit()

    def resizeEvent(self, event):
        #if self.getScale() < self.getMinScale():
        #    self.setScaleAbsolute(0)
        #if self.getScale() > self.getMaxScale():
        #    self.setScaleAbsolute(self.getMaxScale())
        QGraphicsView.resizeEvent(self, event)

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
            scene_view.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
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

def get_dummy_scene():
    scene = QGraphicsScene()
    video = okapy.videoio.FFMPEGIndexedVideoSource("/home/mfischer/data/mika_serien/COUPLING_S1_E1.vob")
    video.getFrame(1000)
    video.getNextFrame()
    img = video.getImage()
    qimg = ogu.toQImage(img, True)
    scene.addPixmap(QPixmap(qimg))
    return (scene, video)

def next_frame():
    for v in videos:
        v.getNextFrame()
    for v, s in zip(videos, scenes):
        img = v.getImage()
        qimg = ogu.toQImage(img, True)
        s.clear()
        s.addPixmap(QPixmap(qimg))

def main():
    app = QApplication(sys.argv)

    for i in range(4):
        (scene, video) = get_dummy_scene()
        videos.append(video)
        scenes.append(scene)

    #viewer = SingleFrameViewer(scene)
    viewer = MultiFrameEqualViewer(scenes)
    viewer.show()
    viewer.resize(800, 600)

    timer = QTimer()
    timer.setInterval(10)
    timer.timeout.connect(next_frame)
    timer.start()

    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())

# Necessary information
# - Functionalities
#   - Display zoom level
