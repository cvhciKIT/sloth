.. highlight:: python

========
Concepts
========

We start by introducing some high-level concepts of Sloth.


Labels
------

Sloth is designed for labeling a set of images or videos.  Each image, or video frame,
can contain any number of labels.  Each label is a set of key-value pairs,
for example::

    {
        "class":  "rect",
        "id":     "Martin",
        "x":      10,
        "y":      30,
        "width":  40,
        "height": 50,
    }

The only required key a label *has* to have is the "class" key.  By convention, the value of "class" is used
to determine the appropriate visualization for this label (in our example it will draw a rectangle).
We will later see, how the mapping between class and visualization can be customized and how custom visualizations
can be added.


Label type conventions
----------------------

Sloth provides support for a range of standard shape labels (for example rectangles, points and polygons).
In order for Sloth to correctly visualize these labels, the labels have to follow
a convention, which keys represent the `x`- and `y`-coordinates, `width` and `height` and so on.

The following simple geometric classes are supported out of the box, i.e.
corresponding visualization items and inserters will be avaible in the default
configuration.

Point
.....
::

    {
        "class": "point",
        "x":     10,
        "y":     20,
    }

Rect
....
::

    {
        "class":   "rect",
        "x":       10,
        "y":       20,
        "width":   20,
        "height":  20,
    }

Polygon
.......
::

    {
        "class": "polygon",
        "xn":    "10;20;30",
        "yn":    "20;30;40",
    }


User defined labels
-------------------

In many cases, labeling requirements extend beyond those simple classes.  Or,
you might want to add further information.  Since each label is just a set of key-value pairs, this
is easily possible by adding more key-value pairs that carry additional information.
For example you can add a key ``type`` that differentiates point labels to be either the label
for the left or the right eye of a face::

    {
        "class": "point",
        "type":  "left_eye",
        "x": 50, "y": 40,
    },
    {
        "class": "point",
        "type":  "right_eye",
        "x": 70, "y": 40,
    }

Of course, you can also create new classes::

    {
        "class": "triangle",
        "x1": 10,
        "y1": 20,
        "x2": 30,
        "y2": 20,
        "x3": 20,
        "y3": 30,
    },
    {
        "class": "deathstar",
        "x": 678,
        "y": 890,
        "z": 666,
        "range": "very far",
        "last_known_message": "What happens if I press *this* button?"
    }

You see in the second example, that the label does not necessarily have to name
a geometric form of any sort.  Neither do the key-value pairs have to denote
only coordinates or attributes.  It can be anything you like.  However, if you
create your own classes you will need to tell the Sloth in the
configuration how to display this label class.  See section :doc:`configuration` on how to do that.


Representation is not storage
-----------------------------

In the sections above we introduced the labels as sets of key-value pairs with
a textual representation.  The storage on disk of the labels however can be
very different.  Sloth does not have *the one* way in which it stores the
labels on-disk.  The labels could be stored as XML, as binary data or in a textual format.
In fact, the labels might not even be stored in a file, but uploaded to a web server.
Again, there are some default formats which the label tool can deal
with out of the box (among others YAML and JSON, which resemble the textual
representation above).  However, you are free to define your own loading and
saving routines for your labels (see :doc:`containers`). This allows you for
example to support legacy third-party label formats (for example one that comes
with a data set) without the need of converting them to JSON first.

