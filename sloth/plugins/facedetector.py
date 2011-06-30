from PyQt4.QtGui import *
from PyQt4.QtCore import *
from sloth.annotations.model import ImageModelItem
from okapy import BinaryPatternFaceDetector

class Worker(QThread):
    valueChanged = pyqtSignal(int)
    def __init__(self, labeltool, det):
        QThread.__init__(self)
        self.labeltool = labeltool
        self.model     = labeltool.model()
        self.det       = det
        self.canceled  = False

    def cancel(self):
        self.canceled = True

    def run(self):
        for i, item in enumerate(self.model.iterator(ImageModelItem)):
            img = self.labeltool.getImage(item)
            faces = self.det.detectFaces(img)
            for face in faces:
                ann = {
                        'class':    'face',
                        'x':        face.box.x,
                        'y':        face.box.y,
                        'width':    face.box.width,
                        'height':   face.box.height,
                        'det_conf': face.conf,
                        }
                item.addAnnotation(ann)
            self.valueChanged.emit(i+1)
            if self.canceled:
                return

class FaceDetectorPlugin(QObject):
    def __init__(self, labeltool):
        QObject.__init__(self)
        self._labeltool = labeltool
        self._wnd = labeltool.mainWindow()
        self._sc  = QAction("Detect faces", self._wnd)
        self._sc.triggered.connect(self.doit)
        self.progress = None
        self.thread   = None

    def on_valueChanged(self, val):
        if self.progress is not None:
            self.progress.setValue(val)

    def on_finished(self):
        self.progress.setValue(self.progress.maximum())
        self.progress.hide()
        self.progress = None
        self.thread   = None
        self._sc.setEnabled(True)

    def doit(self):
        det = BinaryPatternFaceDetector("/cvhci/data/mctcascades/new-detectors/face_frontal_new.xml")
        self._sc.setEnabled(False)
        model = self._labeltool.model()
        n_images = model.rowCount()
        self.progress = QProgressDialog("Detecting faces...", "Abort", 0, n_images, self._wnd);
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.show()
        self.thread = Worker(self._labeltool, det)
        self.progress.canceled.connect(self.thread.cancel)
        self.thread.finished.connect(self.on_finished)
        self.thread.valueChanged.connect(self.on_valueChanged)
        self.thread.start()

    def action(self):
        return self._sc
