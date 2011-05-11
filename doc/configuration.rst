=============
Configuration
=============

The configuration file is a python module where the module-level variables represent the settings.

Settings
========

This is a list of all available settings.

.. _LABELS:

LABELS
------

.. _ITEMS:

ITEMS
-----

.. _HOTKEYS:

HOTKEYS
-------

Default:: `()` (Empty tuple)

Hold a list of hotkeys for the label inserting.  Example::

    (
     ("Point", "",   "",       "p"),
     ("Rect",  "Id", "Martin", "Ctrl+M"),
    )

.. todo:: This sucks! Please come up with a better way to reference the labels.  Also it might be
   interesting to be able to assign hotkeys to other tasks, such as "copy all labels from the previous frame"
   May merge with LABELS, and assign hotkeys there!

.. _INSERTERS:

INSERTERS
---------

Default::

    {
     'rect':    'items.RectInserter',
     'point':   'items.PointInserter',
     'polygon': 'items.PolygonInserter',
    }

Defines a mapping of which inserter should be used for interactively inserting a new label
into the image.  The default inserters allow to draw the respective shape.  Read more 
about how to write your own inserter in :ref:`Inserters`.

.. _LOADERS:

LOADERS
-------

Default::

    {
     'txt':    'loaders.SimpleOneLinerTextLoader',
     'yaml':   'loaders.YamlLoader',
     'pickle': 'loaders.PickleLoader',
    }

Defines a mapping of which loader should be used for loading a label file with the given extension.
This can of course also be a user defined loader.  You can also define the class directly (instead
of a module path)::

    {
     'foo':   MyFooLoader
    }

.. todo::

   What is a better name for LOADERS?  SERIALIZERS?  Because this class should take care of
   writing the labels to the file as well.


.. _PLUGINS:

PLUGINS
-------

Did not think to much about this yet.  This is rather for v2.0.  Could image to be able to define some kind of
plugin that might do some preprocessing on an image, e.g. detect all faces and convert them into labels.

