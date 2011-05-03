RATIOS = ["0.5", "1", "2"]

self.add_label("Rect",    {"type": "rect"})
self.add_label("FixedRatioRect",    {"type": "ratiorect", "_ratio": RATIOS})
self.add_label("Point",   {"type": "point"})
self.add_label("Polygon", {"type": "polygon"})

self.add_hotkey("", "Rect",    "r")
self.add_hotkey("", "Point",   "p")
self.add_hotkey("", "Polygon", "o")
