import os

class AnnotationContainer:
    def __init__(self, loaders):
        self.clear()
        self.loaders_ = dict(loaders)

    def filename(self):
        return self.filename_

    def clear(self):
        self.annotations_ = []
        self.filename_    = None

    def load(self, filename):
        ext = os.path.splitext(filename)[1]
        if ext.startswith('.'):
            ext = ext[1:]

        loader = self.loaders_[ext]()
        self.annotations_ = loader.load(filename)
        self.filename_ = filename

    def save(self, filename):
        pass
        #self.saveRectFormat(filename)

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

