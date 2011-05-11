First Steps
===========

In this section, you will learn with a simple example, how to load labels and write a simple configuration file.
The full configuration options will be covered in the next section :doc:`configuration`.

Using the default configuration
-------------------------------

The easiest way to start is using a supported label format, and supported label types only.  In this case
we just need to start the label tool and supply the label file on the command line::

    ./labeltool.py examples/examplelabels.txt

Let's take look at the example label file::

    image1.jpg type rect x 50 y 80 z 20 type rect x 50 y 80 z 20
    image2.jpg type point x 70 y 80

We have labeled two images, with two rectangles in image1 and one point in image 2.  Since we did not launch
the label tool with a custom configuration, the standard visualizations for rect and point will be used.

Writing a custom configuration
------------------------------

The configuration file is a python module where the module-level variables represent the settings.  The
two most important variable are

  * ITEMS:
  * LABELS: This defines which new labels can be created interactively by the users.

