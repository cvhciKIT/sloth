import sys, os
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class ButtonListWidget(QWidget):
    def __init__(self, name, parent=None):
        QWidget.__init__(self, parent)
        self.name = name
        vlayout = QVBoxLayout()
        vlayout.setSpacing(0)
        vlayout.setAlignment(Qt.AlignTop)
        vlayout.addWidget(QLabel("<center><b>" + name + "</b></center>"))
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(False)
        self.setLayout(vlayout)

    def create_button(self, button_name):
        button = QPushButton(button_name)
        button.setFlat(True)
        button.setCheckable(True)
        button.clicked.connect(self.clickedButton)
        return button

    def add_button(self, button_name):
        button = self.create_button(button_name)
        self.layout().addWidget(button)
        self.button_group.addButton(button)
        return button

    def clickedButton(self):
        for button in self.button_group.buttons():
            if button is not self.sender():
                button.setChecked(False)
        label_name = str(self.sender().text())
        print "sender:", label_name

    def get_checked_button(self):
        return self.button_group.checkedButton()


class ButtonArea(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.label_names = []
        self.label_properties = {}

        self.properties = {}
        self.property_buttons = []

        self.label_button_list = ButtonListWidget("Labels")
        self.property_button_lists = {}
        
        self.hlayout = QHBoxLayout()
        self.hlayout.setAlignment(Qt.AlignLeft)
        self.hlayout.addWidget(self.label_button_list)
        self.setLayout(self.hlayout)
        self.connect(self, SIGNAL('stateChanged(state)'), self.stateChanged)

    def stateChanged(self, state):
        print "stateChanged(state)", state

    def init_button_lists(self):
        for label_name in self.label_names:
            button = self.label_button_list.add_button(label_name)
            button.clicked.connect(self.clickedLabelButton)

        for key, property_values in self.properties.iteritems():
            if key in ["type", "class"]:
                continue
            button_list = ButtonListWidget(key)
            for value in property_values:
                button = button_list.add_button(value)
                button.clicked.connect(self.clickedButton)

            button_list.hide()
            print key
            self.property_button_lists[key] = button_list
            self.hlayout.addWidget(button_list)

    def show_only_label_properties(self, label_name):
        for name, button_list in self.property_button_lists.iteritems():
            if self.label_properties.has_key(label_name) and name in self.label_properties[label_name].keys():
                button_list.show()
            else:
                button_list.hide()
    
    def add_label(self, label_name, properties = {}):
        self.label_names.append(label_name)
        self.label_properties[label_name] = properties
        for key, value in properties.iteritems():
            if self.properties.has_key(key):
                self.properties[key] |= set(value)
            else:
                self.properties[key] = set(value)

    def get_checked_label_button(self):
        return self.label_button_list.get_checked_button()

    def get_current_state(self):
        label_button = self.get_checked_label_button()
        result = {}
        if label_button != None:
            label = str(label_button.text())
            if self.label_properties.has_key(label):
                if self.label_properties[label].has_key("type"):
                    result["type"] = self.label_properties[label]["type"]
                if self.label_properties[label].has_key("class"):
                    result["class"] = self.label_properties[label]["class"]
                for name, button_list in self.property_button_lists.iteritems():
                    if button_list.isVisible():
                        checked_button = button_list.get_checked_button()
                        if checked_button != None:
                            result[button_list.name] = str(checked_button.text())
        return result

    def clickedButton(self):
        button = self.sender()
        print button
        if button.isChecked():
            label_name = str(button.text())
            print label_name
        else:
            print "None"
        self.emit(SIGNAL("stateChanged(state)"), self.get_current_state())

    def clickedLabelButton(self):
        button = self.get_checked_label_button()
        print button
        if button != None:
            label_name = str(button.text())
            print "ButtonArea:", label_name
            self.show_only_label_properties(label_name)
        else:
            print "Selection Mode"
            self.show_only_label_properties("")
        self.emit(SIGNAL("stateChanged(state)"), self.get_current_state())


    def load(self, config_filepath):
        execfile(config_filepath)
        self.init_button_lists()
        
def main():
    app = QApplication(sys.argv)

    ba = ButtonArea()
    ba.load("example_config.py")
    ba.show()

    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())

