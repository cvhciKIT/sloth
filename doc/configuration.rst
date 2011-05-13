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

Default::

    (
     ("Rect",    {"type": "rect"}),
     ("Point",   {"type": "point"}),
     ("Polygon", {"type": "polygon"}),
    )

List of labels.   This will be used to construct the button area from which the user can select to be created
labels.  The second tuple entry is expected to be a python dictionary, which contains at least the key `type`.
All other keys are optional, but are directly used for the newly created label.  A value can also be a list.
In this case, the button area displays another list of options for the key as defined in the list.  Example::

    (
     ("Rect",    {"type": "rect", "class": "head", "id": ["Martin", "Mika", "Boris"]}),
    )

Note two things here.  First, the comma at the end of the first tuple is mandatory.  Otherwise the outer tuple
will not be recognized as one (it will be only parentheses around an object, which will alone not be translated
into a tuple object.  Second, the key `head` does not contain a list as value.  That means, that this key-value
pair will be used directly as such in a newly created label.  For the key `id` the user can choose from the
given list, and only the chosen value will be used for the newly created label.

.. _ITEMS:

ITEMS
-----

Default::

    {
     "rect":    'items.RectItem',
     "point":   'items.PointItem',
     "polygon": 'items.PolygonItem',
    }

Mapping from `type` to the visualization item.  The values need to be python callables that create
a new visualization item. They don't neccessarily need to be subclasses of `AnnotationGraphicsItem`.
Nevertheless, the constructor of any subclass of `AnnotationGraphicItem` is of course a python callable
that creates a new visualization item.

.. _HOTKEYS:

HOTKEYS
-------

Default:: ``()`` (Empty tuple)

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

.. _CONTAINERS:

CONTAINERS
----------

Default::

    {
     '*.txt':    'annotations.container.SimpleOneLinerTextContainer',
     '*.yaml':   'annotations.container.YamlContainer',
     '*.pickle': 'annotations.container.PickleContainer',
    }

Defines a mapping of which container should be used for loading a label file matching the given filename pattern.
This can of course also be a user defined container.  You can also define the class directly (instead
of a module path)::

    {
     '*.foo':   MyFooContainer
    }

.. _PLUGINS:

PLUGINS
-------

Did not think to much about this yet.  This is rather for v2.0.  Could image to be able to define some kind of
plugin that might do some preprocessing on an image, e.g. detect all faces and convert them into labels.

