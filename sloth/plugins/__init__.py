from PyQt4.QtGui import *
from PyQt4.QtCore import *
import logging
LOG = logging.getLogger(__name__)

class CopyAnnotationsPlugin(QObject):
    def __init__(self, labeltool, class_filter=None, frame_range=1, overlap_threshold=None, prefix=''):
        QObject.__init__(self)

        self._class_filter = class_filter
        self._overlap_threshold = overlap_threshold
        self._frame_range = frame_range
        self._prefix = prefix

        self._labeltool = labeltool
        self._wnd = labeltool.mainWindow()
        self._sc  = QAction("Copy labels from previous image/frame", self._wnd)
        self._sc.triggered.connect(self.copy)

    def copy(self):
        current = self._labeltool.currentImage()

        prev = current.getPreviousSibling()
        num_back = self._frame_range

        while num_back > 0 and prev is not None:
            for annotation in self.getAnnotationsFiltered(prev):
                LOG.debug("num_back: %d, annotation: %s", num_back, str(annotation))
                # check for overlap with annotations in current
                if self._overlap_threshold is not None:
                    r1 = self.getRect(annotation)
                    if r1 is not None:
                        cont = False
                        for curr_ann in self.getAnnotationsFiltered(current):
                            r2 = self.getRect(curr_ann)
                            if r2 is not None:
                                o = self.overlap(r1, r2)
                                LOG.debug("overlap between %s and %s: %f", str(r1), str(r2), o)
                                if o > self._overlap_threshold:
                                    cont = True
                                    break
                        if cont:
                            continue # do not copy

                # copy the annotation
                current.addAnnotation(annotation)

            prev = prev.getPreviousSibling()
            num_back -= 1

    def getAnnotationsFiltered(self, image_item):
        annotations = []
        for annotation in image_item.getAnnotations()['annotations']:
            # check class filter
            if self._class_filter is not None:
                if 'class' not in annotation:
                    continue # do not copy
                if annotation['class'] not in self._class_filter:
                    log
                    continue # do not copy
            annotations.append(annotation)
        return annotations

    def getRect(self, annotation):
        keys = ['x', 'y', 'width', 'height']
        for key in keys:
            if not self._prefix + key in annotation:
                return None
        return [annotation[self._prefix + key] for key in keys]

    def overlap(self, r1, r2):
        ia = float(self.area(self.intersect(r1, r2)))
        return min(ia/self.area(r1), ia/self.area(r2))

    def intersect(self, r1, r2):
        x = max(r1[0], r2[0])
        y = max(r1[1], r2[1])
        w = max(0, min(r1[0] + r1[2], r2[0] + r2[2]) - x)
        h = max(0, min(r1[1] + r1[3], r2[1] + r2[3]) - y)
        return (x, y, w, h)

    def area(self, r):
        return r[2]*r[3]

    def action(self):
        return self._sc
