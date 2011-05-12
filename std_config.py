import items
from loaders import FeretLoader, RectIdLoader
from bboxitem import *

RATIOS = ["0.5", "1", "2"]

LABELS = (
    ("Rect",              {"type" : "rect"}),
    ("FixedRatioRect",    {"type": "ratiorect", "_ratio": RATIOS}),
    ("Point",             {"type": "point"}),
    ("Polygon",           {"type": "polygon"}),
    ("BodyBBox",          {"type": "bodybbox"}),
)

HOTKEYS = (
    ("", "Rect",     "r"),
    ("", "Point",    "p"),
    ("", "Polygon",  "o"),
    ("", "BodyBBox", "b")
)

ITEMS = {
    "rect":     items.RectItem,
    "point":    items.PointItem,
    "bodybbox": BodyBoundingboxItem,
}

INSERTERS = {
    "rect":     items.RectItemInserter,
    "bodybbox": BodyBoundingboxItemInserter,
}

LOADERS = (
    ('txt', RectIdLoader),
)

PLUGINS = (
)

