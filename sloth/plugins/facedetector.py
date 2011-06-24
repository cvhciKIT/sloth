from sloth.annotations.model import ImageRole
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from okapy import BinaryPatternFaceDetector

class Worker(QThread):
    valueChanged = pyqtSignal(int)
    def __init__(self, n_images, model, det):
        QThread.__init__(self)
        self.n_images = n_images
        self.model    = model
        self.det      = det
        self.canceled = False

    def cancel(self):
        self.canceled = True

    def run(self):
        for i in range(self.n_images):
            index = self.model.index(i, 0)
            item = self.model.itemFromIndex(index)
            img = item.data(index, ImageRole)
            faces = self.det.detectFaces(img)
            for face in faces:
                ann = {
                        'type':       'rect',
                        'class':      'face',
                        'x':          face.box.x,
                        'y':          face.box.y,
                        'width':      face.box.width,
                        'height':     face.box.height,
                        'confidence': face.conf,
                        }
                self.model.addAnnotation(index, ann)
            self.valueChanged.emit(i+1)
            if self.canceled:
                return

class FaceDetectorPlugin(QObject):
    def __init__(self, wnd):
        QObject.__init__(self, wnd)
        self.wnd_ = wnd
        self.sc_  = QAction("Detect faces", wnd)
        self.sc_.triggered.connect(self.doit)
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
        self.sc_.setEnabled(True)

    def doit(self):
        det = BinaryPatternFaceDetector("/cvhci/data/mctcascades/new-detectors/face_frontal_new.xml")
        self.sc_.setEnabled(False)
        model = self.wnd_.model_
        n_images = model.rowCount()
        self.progress = QProgressDialog("Detecting faces...", "Abort", 0, n_images, self.wnd_);
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.show()
        self.thread = Worker(n_images, model, det)
        self.progress.canceled.connect(self.thread.cancel)
        self.thread.finished.connect(self.on_finished)
        self.thread.valueChanged.connect(self.on_valueChanged)
        self.thread.start()

    def action(self):
        return self.sc_
