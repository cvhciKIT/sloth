import os
import fnmatch
from core.exceptions import ImproperlyConfigured
try:
    import cPickle as pickle
except:
    import pickle

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
        self.containers_ = containers

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
        pass

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
            elif file['type'] == video:
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

