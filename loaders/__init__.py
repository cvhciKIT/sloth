import os

class Loader:
    def __init__(self):
        pass

    def load(self, filename):
        pass

    def save(self, filename, annotations):
        pass

class RectIdLoader(Loader):
    def load(self, filename):
        annotations = []

        print "loading ", filename
        filename_helper = {}

        f = open(filename)
        basedir = ""
        try:
            for line in f:
                s = line.split()
                print s
                image_fname = s[0]
                if basedir == "":
                    basedir = os.path.dirname(image_fname)
                else:
                    assert basedir == os.path.dirname(image_fname)
                num_rects = int(s[1])
                assert num_rects == 0 or num_rects == 1
                if image_fname not in filename_helper:
                    annotation = {
                            'type':     'image',
                            'filename': image_fname,
                            'annotations': []
                            }
                    annotations.append(annotation)
                    filename_helper[image_fname] = annotation

                rects = filename_helper[image_fname]['annotations']

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
        except Exception, e:
            print e

        print annotations
        return annotations

class FeretLoader(Loader):
    def load(self, filename):
        basedir = os.path.dirname(filename)
        f = open(filename)

        annotations = []
        for line in f:
            s = line.split()
            fileitem = {
                'filename': os.path.join(basedir, s[0]+".bmp"),
                'type': 'image',
            }
            fileitem['annotations'] = [
                {'type': 'point', 'class': 'left_eye',  'x': int(s[1]), 'y': int(s[2])},
                {'type': 'point', 'class': 'right_eye', 'x': int(s[3]), 'y': int(s[4])},
                {'type': 'point', 'class': 'mouth',     'x': int(s[5]), 'y': int(s[6])}
            ]
            annotations.append(fileitem)

        return annotations

