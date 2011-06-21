.. highlight:: python

===========
First Steps
===========

In this section, you will learn with a simple example, how to load labels and
write a simple configuration file.  The full configuration options will be
covered in the next section :doc:`configuration`.

Using the default configuration
===============================

The easiest way to start sloth is by using a supported label format and
supported label types only.  In this case we just need to start sloth and
supply the label file on the command line::

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

We have labeled two images, with two rectangles in image1 and one point in
image 2.  Since we launched sloth without a custom configuration, the standard
visualizations for ``rect`` and ``point`` will be used. Sloth displays two
rectangles at the labeled positions in image1, and a point in image2.

Adding and editing annotation in the GUI
========================================

TODO

Writing a custom configuration
==============================

The configuration file is a python module where the module-level variables
represent the settings.  The most important variable is

* :ref:`LABELS`:    This defines how sloth will display annotations and how the
  user can insert new ones.

We start with a quick example::

    LABELS = (
        {"attributes": {"type":  "rect",
                        "class": "head",
                        "id":    ["Martin", "Mika"]},
         "item":     "sloth.items.RectItem",
         "inserter": "sloth.items.RectItemInserter",
         "text:      "Head"
        },

        {"attributes": {"type":  "point",
                        "class": "left_eye",
                        "id":    ["Martin", "Mika"]},
         "item":     "sloth.items.PointItem",
         "inserter": "sloth.items.PointItemInserter",
         "text:      "Left Eye"
        },

        {"attributes": {"type":  "point",
                        "class": "right_eye",
                        "id":    ["Martin", "Mika"]},
         "item":     "sloth.items.PointItem",
         "inserter": "sloth.items.PointItemInserter",
         "text:      "Right Eye"
        },
    )

``LABELS`` is a tuple/list of dictionaries.  Each dictionary describe how one
annotation type is visualized, newly inserted and modified.  Let's go over the
different keys of the dictionary in detail:

* ``text``:  This is a text that describes the label type, and will be
  displayed to the user in the GUI.

* ``item`` specifies which class is responsible for visualizing the annotation.
  For the first annotation type we chose to use the predefined
  ``sloth.items.RectItem`` class, which will draw a rectangle as given by the
  coordinates in the annotation.  Sloth comes with several predefined
  visualization classes, such as ``sloth.items.RectItem`` and
  ``sloth.items.PointItem`` (see :ref:`items` for a full list).  However, it is
  also very easy to define your own visualization class (see :ref:`items`).

* ``inserter`` specifies which class is responsible for creating new
  annotations based on user input.  When the user enters insert mode with a
  given label type, the corresponding inserter is instantiated and captures all
  user input for the creation of a new annotation.  The inserter is passed the
  current state of the button area.

* ``attributes`` has three functions:
  1. It defines how a new annotation can be initialized.  Fixed
     key-value pairs are used directly.  If the value is a list of items, the
     user can choose interactively which one of the values he wants to use for
     a new label.  The current state is then passed to the inserter.

  2. It defines how a existing annotations can be edited.  Fixed
     key-value are not allowed to be edited.  If the value is a list of items, the
     user can choose interactively between the values for the corresponding key.
     The annotation is then updated accordingly.

  3. It defines how to match an existing annotation to one of the entries in ``LABELS``.
     Sloth uses a soft matching based on the two keys ``class`` and ``type``.  It checks
     each item in ``LABELS`` starting from the beginning and stops if it finds the first
     match.  An entry matches an annotation if:

       * the values for both keys match, or
       * the value for one of keys matches and the other key is not present in
         either ``attributes`` or the annotation.

You need to save your custom configuration in a file ending with ".py".  To use it
pass it to sloth using the ``--config`` command line parameter::

    sloth --config myconfig.py examples/example1_labels.json

You can now start labeling head locations and eye positions.  You'll see that for each 
depending on the chosen annotation, you can either insert a rectangle (this is internally
done by the ``RectItemInserter``) or points (using the ``PointItemInserter``).  For
each annotation you can choose an identity between the two supplied options.

Next steps
==========

You can now continue by reading about :doc:`all available configuration options <configuration>`,
how to write your own :doc:`visualization items <items>` or how to write :doc:`custom inserters <inserters>`.

