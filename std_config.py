from items import AnnotationGraphicsRectItem as RectItem 
from items import RectItemInserter, AnnotationGraphicsPointItem
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

ITEMS = (
    ("rect",     RectItem),
    ("point",    AnnotationGraphicsPointItem),
    ("bodybbox", BodyBoundingboxItem),
)

INSERTERS = (
    ("rect",     RectItemInserter),
    ("bodybbox", BodyBoundingboxItemInserter),
)

LOADERS = (
    ('txt', RectIdLoader),
)

PLUGINS = (
)

#labeltool.buttonarea.add_label("Rect",     {"type": "rect"})
#labeltool.buttonarea.add_label("FixedRatioRect",    {"type": "ratiorect", "_ratio": RATIOS})
#labeltool.buttonarea.add_label("Point",    {"type": "point"})
#labeltool.buttonarea.add_label("Polygon",  {"type": "polygon"})
#labeltool.buttonarea.add_label("BodyBBox", {"type": "bodybbox"})
#
#Labeltool.buttonarea.add_hotkey("", "Rect",     "r")
#Labeltool.buttonarea.add_hotkey("", "Point",    "p")
#Labeltool.buttonarea.add_hotkey("", "Polygon",  "o")
#Labeltool.buttonarea.add_hotkey("", "BodyBBox", "b")

