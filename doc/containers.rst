.. highlight:: python

==========
Containers
==========

Annotation containers provide functions for loading and saving labels.  You can
write custom containers to support specific label formats.

Container Interface
===================

A container is expected to implement (at least) these five functions:

.. py:function:: load(self, filename)

    Loads and returns the annotations in file ``filename``.

.. py:function:: save(self, annotations, filename)

    Writes the given annotations to file ``filename``.

.. py:function:: filename(self)

    Returns the current filename.

.. py:function:: loadImage(self, filename)

    Loads and returns the image referenced to by filename

.. py:function:: loadFrame(self, filename, frame_number)

    Load the video referenced to by the filename, and return frame
    ``frame_number``.

The container base class ``AnnotationContainer`` provides default
implementations for all five function.  It however defers the
parsing and serialization of the labels from/to disk to the two functions

.. py:function:: parseFromFile(self, filename)

and

.. py:function:: serializeToFile(self, filename, annotations)

respectively.  If you subclass AnnotationContainer, make sure to
provide implementations for those two functions.


Default Containers
==================

A few containers are included in Sloth.  They can be found in the module
``sloth.annotations.container``.  In the default configuration, these
containers are included for their respective default filename pattern.

JsonContainer
-------------

Default pattern: ``*.json``

Writes and reads annotations in JSON format (needs the python module ``json``
to be installed).

YamlContainer
-------------

Default pattern: ``*.yaml``

Writes and reads annotations in YAML format (needs the python module ``yaml``
to be installed).

MsgpackContainer
----------------

Default pattern: ``*.msgpack``

Writes and reads annotations in Msgpack format (needs the python module ``msgpack``
to be installed).

PickleContainer
---------------

Default pattern: ``*.pickle``

Writes and reads annotations in pickle format (needs the python module ``pickle``
or ``cPickle`` to be installed, ``cPickle`` is more performant).

FileNameListContainer
---------------------

Default pattern: ``*.sloth-init``

A simple container that reads one image filename per line.  No annotations
are supported.  This container can be used for example for initializing 
a labeling session.  After adding labels, another container should be 
used for saving though, otherwise the labels will be lost (write support
is not implemented).

FeretContainer
--------------

Reads annotations in the Feret format (no write support implemented yet).
This container is not included in the default configuration.

