import os
import glob

class AnnotationContainer:
    def __init__(self):
        self.clear()

    def filename(self):
        return self.filename_

    def clear(self):
        self.annotations_ = []
        self.filename_    = None

    def load(self, filename):
        self.loadRectFormat(filename)

    def loadRectFormat(self, filename):
        self.annotations_ = []
        self.filename_ = filename
        filename_helper = {}

        try:
            f = open(filename)
            basedir = ""
            for line in f:
                s = line.split()
                image_fname = s[0]
                if basedir == "":
                    basedir = os.path.dirname(image_fname)
                else:
                    assert basedir == os.path.dirname(image_fname)
                num_rects = int(s[1])
                assert num_rects == 0 or num_rects == 1
                if image_fname in filename_helper:
                    rects = filename_helper[image_fname]['annotations']
                else:
                    rects = []

                for i in range(0, 4*num_rects, 4):
                    rects.append({
                        'type': 'rect',
                        'x': s[i+2],
                        'y': s[i+3],
                        'width':  s[i+4],
                        'height': s[i+5]
                        })
                    if len(s) > i+6:
                        rects[-1]['id'] = s[i+6]

                if image_fname not in filename_helper:
                    annotation = {
                            'type':     'image',
                            'filename': image_fname,
                            'annotations': rects
                            }
                    self.annotations_.append(annotation)
                    filename_helper[image_fname] = annotation
        except Exception as e:
            self.annotations_ = []
            raise e

        basedir1 = basedir
        basedir = os.path.join(os.path.dirname(filename), basedir)
        images = glob.glob(os.path.join(basedir, "*.png"))
        for fname in images:
            fname = os.path.join(basedir1, os.path.basename(fname))
            if fname not in filename_helper:
                print fname, "not in filename_helper"
                annotation = {
                        'type':     'image',
                        'filename': fname,
                        'annotations': []
                        }
                self.annotations_.append(annotation)
    
    def save(self, filename):
        self.saveRectFormat(filename)

    def saveRectFormat(self, filename):
        f = open(filename, "w")

        for file in self.annotations_:
            if file['type'] == 'image':
                rect_anns = [ann for ann in file['annotations'] if ann['type'] == 'rect']
                #f.write("%s %d", file['filename'], len(rect_anns))
                for ann in rect_anns:
                    f.write('%s 1 %s %s %s %s %s\n' % (file['filename'], str(ann['x']), str(ann['y']), str(ann['width']), str(ann['height']), str(ann.get('id', ""))))
                if len(rect_anns) == 0:
                    f.write('%s 0\n' % (file['filename']))

        self.filename_ = filename

    def asDict(self):
        return self.annotations_

    def numFiles(self):
        return len(self.annotations_)

    def numAnnotations(self):
        if self.annotations_ is None:
            return 0
        num = 0
        for file in self.annotations_:
            if file['type'] == 'image':
                num += len(file['annotations'])
            elif file['type'] == video:
                for frame in file['frames']:
                    num += len(frame['annotations'])
        return num

