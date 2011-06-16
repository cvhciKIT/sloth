LABELS = (
    ('Rect',  {'type': 'rect'}),
    ('Point', {'type': 'point'}),
)

HOTKEYS = (
        ('PgDown',    lambda lt: lt.gotoNext(),                 'Next image/frame'),
        ('PgUp',      lambda lt: lt.gotoPrevious(),             'Previous image/frame'),
        ('Tab',       lambda lt: lt.selectNextAnnotation(),     'Select next annotation'),
        ('Shift+Tab', lambda lt: lt.selectPreviousAnnotation(), 'Select previous annotation'),
        ('ESC',       lambda lt: lt.exitInsertMode(),           'Exit insert mode'),
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

