.. highlight:: python

===========
First Steps
===========

In this section, you will learn with a simple example, how to load labels and write a simple configuration file.
The full configuration options will be covered in the next section :doc:`configuration`.

Using the default configuration
===============================

The easiest way to start sloth is by using a supported label format and supported label types only.  In this case
we just need to start sloth and supply the label file on the command line::

    sloth examples/example1_labels.json

Let's take look at the example label file::

    [
        {
            "type": "image", 
            "annotations": [
                {
                    "height": 60.0, 
                    "width": 46.0, 
                    "y": 105.0, 
                    "x": 346.0, 
                    "type": "rect"
                }, 
                {
                    "height": 58.0, 
                    "width": 56.0, 
                    "y": 119.0, 
                    "x": 636.0, 
                    "type": "rect"
                }
            ], 
            "filename": "image1.jpg"
        }, 
        {
            "type": "image", 
            "annotations": [
                {
                    "y": 155.0, 
                    "x": 409.0, 
                    "type": "point"
                }
            ], 
            "filename": "image2.jpg"
        }
    ]

We have labeled two images, with two rectangles in image1 and one point in image 2.  Since we launched
sloth without a custom configuration, the standard visualizations for ``rect`` and ``point`` will be used. Sloth
displays two rectangles at the labeled positions in image1, and a point in image2.

Writing a custom configuration
==============================

The configuration file is a python module where the module-level variables represent the settings.  The
most important variables are

* :ref:`ITEMS`:     This defines how a given label is visualized by the label tool.
* :ref:`LABELS`:    This defines *which* new labels can be created interactively by the user.
* :ref:`INSERTERS`: This defines *how* new labels are created by the user.

We start with a quick example::

    ITEMS = {
        'rect':  'items.RectItem',
        'point': 'items.PointItem',
        'bbox':  'items.RectItem',
    }

    LABELS = (
        ("Rect",          {"type":  "rect",
                           "class": "head",
                           "id":    ["Martin", "Mika"]}),
        ("Bounding Box",  {"type":  "bbox",
                           "class": "body",
                           "id":    ["Martin", "Mika"]}),
    )

In ``ITEMS`` we specify that all labels of type ``rect`` will be visualized by the class ``items.RectItem``
(which is one of the predefined visualization items that comes with the label tool).  All labels of type
``point`` will be visualized by ``items.PointItem``.  Note that we can use any type basically.  The type 
``bbox`` will also be visualized by a ``items.RectItem``.

In ``LABELS`` we defined which `new` labels the user can create with the label tool.  The variable is
expected to be a list/tuple of tuples.  Each of the inner tuples contains first a description of the
label (this will be on the button displayed to the user), and the a description of the label to be 
created.  In our case, we create a label of type ``rect`` if the user hits the ``Rect`` button.  Further,
the newly created label will have the class ``head`` (which is fixed), and the user can choose between
one of the ids from the given list.

Similarly, the user now can create Bounding Box labels of type ``bbox`` with class ``body``.

There is a difference between the visualization items and the way the labels are created by the user 
interactively.  For example, the label tool does *not* know out of the box how to create a label of
type ``bbox``.  We have to explicitly specify how to insert this type.  We can do this by setting
the ``INSERTERS`` variable::

    INSERTERS = {
        'rect':  'items.inserters.RectItemInserter',
        'bbox':  'items.inserters.RectItemInserter',
    }

The ``RectItemInserter`` lets the user draw a rectangle with the mouse, and then sets the ``x``,
``y``, ``width`` and ``height`` members of the label accordingly.  By mapping the type ``bbox``
to ``RectItemInserter``, the user will be able to draw a rectangle each time a new Bounding Box
label is created.  Note that we also have to add the ``RectItemInserter`` for the type ``rect``
as well (which would also be in the default configuration)  due to the fact that we override
the ``INSERTERS`` variable completely.  Otherwise the label tool would not know anymore, how
to insert labels of type ``rect``.

In order to extend the default configuration and avoid overriding the default values, you can
first import the default configuration and then append your custom mappings (remember that
the configuration is a python module, you can basically execute any valid python code)::

    from conf.default_configuration import INSERTERS
    INSERTERS['bbox'] = 'items.inserters.RectItemInserter'

You can now continue by reading about :doc:`all available configuration options <configuration>`,
how to write your own :doc:`visualization items <items>` or how to write :doc:`custom inserters <inserters>`.

