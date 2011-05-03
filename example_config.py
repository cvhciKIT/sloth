obj_type_choice = ["Apple", "Chair", "Carpet"]
obj_type_choice2 = ["Peach", "Table", "Window"]

ID_choice = ["Martin", "Mika", "Alexander", "Lukas", "Tobias"]
ID_choice2 = ["Boris", "Manel", "Rainer", "Hua", "Hazim"]

self.add_label("Head", {"type": "rect",
                        "class": "head",
                        "id": ID_choice})
self.add_label("Left Eye", {"type": "point",
                            "class": "left_eye",
                            "id": ID_choice,
                            "obj_type": obj_type_choice})
self.add_label("Right Eye", {"type": "point",
                             "class": "right_eye",
                             "id": ID_choice2,
                             "obj_type": obj_type_choice2})
self.add_label("Left Hand", {"type": "rect",
                             "class": "left_hand",
                             "obj_type": obj_type_choice})
self.add_label("Right Hand", {"type": "rect",
                              "class": "right_hand"})

self.add_hotkey("",   "Head",   "h")
self.add_hotkey("id", "Martin", "CTRL+m")
