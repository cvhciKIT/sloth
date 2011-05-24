import os
import fnmatch
from sloth.core.exceptions import ImproperlyConfigured, NotImplementedException
from sloth.core.utils import import_callable
try:
    import cPickle as pickle
except:
    import pickle
try:
    import json
except:
    pass
try:
    import yaml
except:
    pass

class AnnotationContainerFactory:
    def __init__(self, containers):
        """
        Initialize the factory with the mappings between file pattern and
        the container.

        Parameters
        ==========
        containers: tuple of tuples (str, str/class)
            The mapping between file pattern and container class responsible
            for loading/saving.
        """
        self.containers_ = []
        for pattern, item in containers:
            if type(item) == str:
                item = import_callable(item)
            self.containers_.append((pattern, item))

    def create(self, filename, *args, **kwargs):
        """
        Create a container for the filename.

        Parameters
        ==========
        filename: str
            Filename for which a matching container should be created.
        *args, **kwargs:
            Arguments passed to constructor of the container.
        """
        for pattern, container in self.containers_:
            if fnmatch.fnmatch(filename, pattern):
                return container(*args, **kwargs)
        raise ImproperlyConfigured("No container registered for filename %s" % filename)

class AnnotationContainer:
    def __init__(self):
        self.clear()

    def filename(self):
        return self.filename_

    def clear(self):
        self.annotations_ = []
        self.filename_    = None

    def load(self, filename):
        """
        Load the annotations.  Must be implemented in the subclass.
        """
        pass

    def save(self, filename):
        """
        Save the annotations.  Must be implemented in the subclass.
        """
        pass

    def annotations(self):
        """
        Returns the current annotations as python dictionary.
        """
        return self.annotations_

    def loadImage(self, filename):
        """
        Load the image referenced to by the filename.  In the default
        implementation this will try to load the image from a path
        relative to the label files directory.
        """
        return okapy.loadImage(filename)

    def loadVideo(self, filename):
        """
        Load the video referenced to by the filename.  In the default
        implementation this will try to load the video from a path
        relative to the label files directory.
        """
        pass

    def setAnnotations(self, annotations):
        self.annotations_ = annotations

    def numFiles(self):
        return len(self.annotations_)

    def numAnnotations(self):
        if self.annotations_ is None:
            return 0
        num = 0
        for file in self.annotations_:
            if file['type'] == 'image':
                num += len(file['annotations'])
            elif file['type'] == 'video':
                for frame in file['frames']:
                    num += len(frame['annotations'])
        return num

class PickleContainer(AnnotationContainer):
    """
    Simple container which just pickles the annotations to disk.
    """

    def load(self, fname):
        f = open(fname, "rb")
        self.annotations_ = pickle.load(f)
        self.filename_ = fname

    def save(self, fname):
        f = open(fname, "wb")
        pickle.dump(self.annotations(), f)
        self.filename_ = fname

class JSONContainer(AnnotationContainer):
    """
    Simple container which writes the annotations to disk in JSON format.
    """

    def load(self, fname):
        f = open(fname, "r")
        self.annotations_ = json.load(f)
        self.filename_ = fname

    def save(self, fname):
        f = open(fname, "w")
        json.dump(self.annotations(), f, indent=4)
        self.filename_ = fname

class YAMLContainer(AnnotationContainer):
    """
    Simple container which writes the annotations to disk in YAML format.
    """

    def load(self, fname):
        f = open(fname, "r")
        self.annotations_ = yaml.load(f)
        self.filename_ = fname

    def save(self, fname):
        f = open(fname, "w")
        yaml.dump(self.annotations(), f, indent=4)
        self.filename_ = fname

class FeretContainer(AnnotationContainer):
    """
    Container for Feret labels.
    """

    def load(self, filename):
        self.basedir_ = os.path.dirname(filename)
        f = open(filename)

        annotations = []
        for line in f:
            s = line.split()
            fileitem = {
                'filename': os.path.join(self.basedir_, s[0]+".bmp"),
                'type': 'image',
            }
            fileitem['annotations'] = [
                {'type': 'point', 'class': 'left_eye',  'x': int(s[1]), 'y': int(s[2])},
                {'type': 'point', 'class': 'right_eye', 'x': int(s[3]), 'y': int(s[4])},
                {'type': 'point', 'class': 'mouth',     'x': int(s[5]), 'y': int(s[6])}
            ]
            annotations.append(fileitem)

        self.annotations_ = annotations
        self.filename_    = filename


    def save(self, filename):
        # TODO make sure the image paths are relative to the label file's directory
        raise NotImplemented("FeretContainer.save() is not implemented yet.")




