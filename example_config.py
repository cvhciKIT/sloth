obj_type_choice = ["Apple", "Chair", "Carpet"]
obj_type_choice2 = ["Peach", "Table", "Window"]

ID_choice = ["Martin", "Mika", "Alexander", "Lukas", "Tobias"]
ID_choice2 = ["Boris", "Manel", "Rainer", "Hua", "Hazim"]

LABELS = (
    ("Head", {"type": "rect",
              "class": "head",
              "id": ID_choice}),
    ("Left Eye", {"type": "point",
                  "class": "left_eye",
                  "id": ID_choice,
                  "obj_type": obj_type_choice}),
    ("Right Eye", {"type": "point",
                   "class": "right_eye",
                   "id": ID_choice2,
                   "obj_type": obj_type_choice2}),
    ("Left Hand", {"type": "rect",
                   "class": "left_hand",
                   "obj_type": obj_type_choice}),
    ("Right Hand", {"type": "rect",
                              "class": "right_hand"}),
)

HOTKEYS = (
    ("",   "Head",   "h"),
    ("id", "Martin", "CTRL+m"),
)
