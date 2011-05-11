.. highlight:: python

Concepts
========

Labels
------

The label tool is designed for labeling a set of image files or videos.  Each image, or video frame,
can contain any number of labels.  The labels itself are expected to be sets key-value pairs.  We can
therefore represent a label for example in the following way::

    {
        type:   "rect",
        id:     "Martin",
        x:      10,
        y:      30,
        width:  40,
        height: 50,
    }

The only required key a label *has* to have is the "type" key.  It will be used by the label tool
to determine the appropriate visualization for this label (in our example it will draw a rect).
We will later see, how you can customize the mapping between type and visualization and how to
write your own visualizations.

Label type conventions
----------------------

The label tool provides support for a range of standard shape label (for example `rect`, `point`, `polygon` etc.).
In order for the label tool to correctly visualize these labels, the labels have to follow
a convention, which the keys are for `x`- and `y`-coordinates, `width` and `height` and so on.

The following types are supported out of the box

Point
.....

::

    {
        type: "point",
        x:    10,
        y:    20,
    }

Rect
....

::

    {
        type:   "rect",
        x:      10,
        y:      20,
        width:  20,
        height: 20,
    }

Polygon
.......

::

    {
        type:   "polygon",
        xn:     "10;20;30",
        yn:     "20;30;40",
    }

User defined labels
-------------------

For many cases, it might suffice to use the predefined labels.  But as 


Representation is not storage
-----------------------------

In the sections above we introduced the labels as sets of key-value pairs with a textual representation.
The storage on disk of the labels however can be very different.
The label tool does not have *the one* in which way to store the labels.  Again,
there are some default formats with which the label tool can deal out of the box (one of
which will be a yaml file, which resembles the textual representation above).  However,
you are free to define your own loading and saving routines for your labels (see ***). This
allows you for example to support legacy third-party label formats without the need to convert 
them first.

