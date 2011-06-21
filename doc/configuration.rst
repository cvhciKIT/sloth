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
        {
            'attributes': {
                'type':      'rect',
             },
            'inserter': 'sloth.items.RectItemInserter',
            'item':     'sloth.items.RectItem',
            'hotkey':   'r',
            'text':     'Rectangle',
        },
        {
            'attributes': {
                'type':    'point',
            },
            'inserter': 'sloth.items.PointItemInserter',
            'item':     'sloth.items.PointItem',
            'hotkey':   'p',
            'text':     'Point',
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


Note that the comma at the end of the first tuple is mandatory.  Otherwise the
outer tuple will not be recognized as one (it will be only parentheses around
an object, which will alone not be translated into a tuple object.  This
applies similarly to all tuple/list-type settings.

.. _HOTKEYS:

HOTKEYS
-------

Default::

    (
        ('PgDown',    lambda lt: lt.gotoNext(),                  'Next image/frame'),
        ('PgUp',      lambda lt: lt.gotoPrevious(),              'Previous image/frame'),
        ('Tab',       lambda lt: lt.selectNextAnnotation(),      'Select next annotation'),
        ('Shift+Tab', lambda lt: lt.selectPreviousAnnotation(),  'Select previous annotation'),
        ('Del',       lambda lt: lt.deleteSelectedAnnotations(), 'Delete selected annotations'),
        ('ESC',       lambda lt: lt.exitInsertMode(),            'Exit insert mode'),
    )

Defines global keyboard shortcuts.  Each hotkey is defined by a tuple with at
least 2 entries, where the first entry is the hotkey (sequence), and the second
entry is the function that is called.  The function should expect a single
parameter, the labeltool object.  The optional third entry -- if present -- is
expected to be a string describing the action.

.. _CONTAINERS:

CONTAINERS
----------

Default::

    {
     '*.txt':    'annotations.container.SimpleOneLinerTextContainer',
     '*.yaml':   'annotations.container.YamlContainer',
     '*.pickle': 'annotations.container.PickleContainer',
    }

Defines a mapping of which container should be used for loading a label file
matching the given filename pattern.  This can of course also be a user defined
container.  You can also define the class directly (instead of a module path)::

    {
     '*.foo':   MyFooContainer
    }

.. _PLUGINS:

PLUGINS
-------

Did not think to much about this yet.  This is rather for v2.0.  Could image to be able to define some kind of
plugin that might do some preprocessing on an image, e.g. detect all faces and convert them into labels.


Extending default values
========================

In the usual case one overrides the default when defining a setting
variable.  In order to extend the default configuration and avoid overriding
the default values, you can first import the default configuration and then
append your custom mappings (remember that the configuration is a python
module, you can basically execute any valid python code)::

    from conf.default_config import LABELS

    MYLABLES = ({
       ...
    })

    LABELS += MYLABELS

