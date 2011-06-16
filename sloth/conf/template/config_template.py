# Sloth configuration.
#
# The configuration file is a simple python module with module-level
# variables.  This module contains the default values for sloth's 
# configuration variables.
#
# In all cases in the configuration where a python callable (such as a
# function, class constructor, etc.) is expected, it is equally possible
# to specify a module path (as string) pointing to such a python callable.
# It will then be automatically imported.

# LABLES
#
# List/tuple of dictionaries that defines the label types
# that are handled by sloth.  For each label, there should
# be one dictionary that contains the following keys:
#
#   - 'item' : Visualization item for this label. This can be
#              any python callable or a module path string 
#              implementing the visualization item interface.
#
#   - 'inserter' : (optional) Item inserter for this label.
#                  If the user selects to insert a new label of this type
#                  the inserter is responsible to actually 
#                  capture the users mouse actions and insert
#                  a new label into the annotation model.
#
#   - 'hotkey' : (optional) A keyboard shortcut starting 
#                the insertion of a new label of this type.
#
#   - 'attributes' : (optional) A dictionary that defines the
#                    keys and possible values of this label
#                    type.
LABELS = (
    {
        'attributes': {
            'type':      'rect',
         },
        'inserter': 'sloth.items.RectItemInserter',
        'item':     'sloth.items.RectItem',
        'hotkey':   'r',
    },
    {
        'attributes': {
            'type':    'point',
        },
        'inserter': 'sloth.items.PointItemInserter',
        'item':     'sloth.items.PointItem',
        'hotkey':   'p',
    },
)

# HOTKEYS
#
# Defines the keyboard shortcuts.  Each hotkey is defined by a tuple
# with at least 2 entries, where the first entry is the hotkey (sequence),
# and the second entry is the function that is called.  The function
# should expect a single parameter, the labeltool object.  The optional
# third entry -- if present -- is expected to be a string describing the 
# action.
HOTKEYS = (
    ('PgDown',    lambda lt: lt.gotoNext(),                 'Next image/frame'),
    ('PgUp',      lambda lt: lt.gotoPrevious(),             'Previous image/frame'),
    ('Tab',       lambda lt: lt.selectNextAnnotation(),     'Select next annotation'),
    ('Shift+Tab', lambda lt: lt.selectPreviousAnnotation(), 'Select previous annotation'),
    ('ESC',       lambda lt: lt.exitInsertMode(),           'Exit insert mode'),
)

# CONTAINERS
#
# A list/tuple of two-tuples defining the mapping between filename pattern and
# annotation container classes.  The filename pattern can contain wildcards
# such as * and ?.  The corresponding container is expected to either a python
# class implementing the sloth container interface, or a module path pointing
# to such a class.
CONTAINERS = (
    ('*.json',       'sloth.annotations.container.JsonContainer'),
    ('*.yaml',       'sloth.annotations.container.YamlContainer'),
    ('*.pickle',     'sloth.annotations.container.PickleContainer'),
    ('*.sloth-init', 'sloth.annotations.container.FileNameListContainer'),
)

# PLUGINS
#
# A list/tuple of classes implementing the sloth plugin interface.  The
# classes can either be given directly or their module path be specified 
# as string.
PLUGINS = (
)

