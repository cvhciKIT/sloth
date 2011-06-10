# Import defaults.
# You can either overwrite or modify the defaults to your liking.
from sloth.conf.default_config import *

LABELS = (
    ('Rect',  {'type': 'rect'}),
    ('Point', {'type': 'point'}),
)

HOTKEYS = (
)

# Defines the mapping from the annotation type to the visualization item. The
# values need to be either python callables, or a module path string that
# points to a python callable. The callable is responsible for creating and
# returning the corresponding visualization item.
ITEMS = {
    'rect':  'sloth.items.RectItem',
    'point': 'sloth.items.PointItem',
}

INSERTERS = {
    'rect':  'sloth.items.RectItemInserter',
    'point': 'sloth.items.PointItemInserter',
}

CONTAINERS = (
    ('*.json',       'sloth.annotations.container.JsonContainer'),
    ('*.yaml',       'sloth.annotations.container.YamlContainer'),
    ('*.pickle',     'sloth.annotations.container.PickleContainer'),
    ('*.sloth-init', 'sloth.annotations.container.FileNameListContainer'),
)

PLUGINS = (
)

