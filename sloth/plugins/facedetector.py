from sloth.annotations.model import ImageRole
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from okapy import BinaryPatternFaceDetector

class FaceDetectorPlugin(QObject):
    def __init__(self, wnd):
        QObject.__init__(self, wnd)
        self.wnd_ = wnd
        self.sc_  = QAction("Detect faces", wnd)
        self.sc_.triggered.connect(self.doit)

    def doit(self):
        print "Loading detector..."
        det = BinaryPatternFaceDetector("/cvhci/data/mctcascades/new-detectors/face_frontal_new.xml")
        model = self.wnd_.model_
        n_images = model.rowCount()
        progress = QProgressDialog("Detecting faces...", "Abort", 0, n_images, self.wnd_);
        progress.setWindowModality(Qt.WindowModal);
        progress.show()

        for i in range(n_images):
            index = model.index(i, 0)
            item = model.itemFromIndex(index)
            img = item.data(index, ImageRole)
            faces = det.detectFaces(img)
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
                model.addAnnotation(index, ann)
            progress.setValue(i+1);
            QCoreApplication.processEvents()
            if progress.wasCanceled():
                break

    def action(self):
        return self.sc_
