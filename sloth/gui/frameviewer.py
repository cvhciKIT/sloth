import math
from PyQt4.QtCore import *
from PyQt4.QtGui import *
try:
    import okapy.videoio
except ImportError:
    pass

videos = []
scenes = []


class GraphicsView(QGraphicsView):
    # Signals
    scaleChanged = pyqtSignal(float)
    focusIn = pyqtSignal()

    def __init__(self, parent=None):
        QGraphicsView.__init__(self, parent)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        #self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setMouseTracking(True)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
        self.setStyleSheet("QFrame { border: 3px solid black }")
        self._active = False
        self._pan = False
        self._panStartX = -1
        self._panStartY = -1

        # Windows photo viewer like controls
        self.setRenderHints(QPainter.Antialiasing|QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    def fitInView(self):
        if self.scene() is None:
            return
        si = self.scene().sceneItem()
        if si is None:
            return

        old_scale = self.getScale()
        QGraphicsView.fitInView(self, si, Qt.KeepAspectRatio)
        new_scale = self.getScale()

        if new_scale != old_scale:
            self.scaleChanged.emit(new_scale)

    def setScene(self, scene):
        QGraphicsView.setScene(self, scene)
        #self.setScaleAbsolute(1)

    def getScale(self):
        if self.isTransformed():
            return self.transform().m11()
        else:
            return 1

    def isActive(self):
        return self._active

    def activate(self):
        if not self._active:
            self._active = True
            self.setFocus(Qt.OtherFocusReason)
            self.setStyleSheet("QFrame { border: 3px solid red }")
            self.update()

    def deactivate(self):
        if self._active:
            self._active = False
            self.clearFocus()
            self.setStyleSheet("QFrame { border: 3px solid black }")
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

    def mousePressEvent(self, event):
        if event.button() & Qt.MidButton != 0:
            self._pan = True
            self._panStartX = event.x()
            self._panStartY = event.y()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            return QGraphicsView.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self._pan:
            self._pan = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            return QGraphicsView.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        if self._pan:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - (event.x() - self._panStartX))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - (event.y() - self._panStartY))
            self._panStartX = event.x()
            self._panStartY = event.y()
            event.accept()
        else:
            return QGraphicsView.mouseMoveEvent(self, event)


class FrameViewer(QWidget):
    # Signals
    activeSceneViewChanged = pyqtSignal(GraphicsView)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

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
            self.layout.addWidget(scene_view, i/n_cols, i % n_cols)
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
