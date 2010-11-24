import sys, os
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class ButtonArea(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.label_names = []
        self.label_properties = {}

        self.properties = {}
        self.property_buttons = []
        
        self.last_checked_label = None
        
    def create_button(self, button_name):
        button = QPushButton(button_name)
        button.setFlat(True)
        button.setCheckable(True)
        button.clicked.connect(self.clickedButton)
        return button

    def update_label_buttons(self):
        label_vlayout = self.create_choice_list("Labels")
        self.label_buttongroup = QButtonGroup()
        for label_name in self.label_names:
            button = QPushButton(label_name)
            button.setFlat(True)
            button.setCheckable(True)
            button.clicked.connect(self.clickedLabelButton)
            label_vlayout.addWidget(button)
            self.label_buttongroup.addButton(button)
            if label_name == self.last_checked_label:
                button.setChecked(True)

        self.hlayout = QHBoxLayout()
        self.hlayout.addLayout(label_vlayout)
        self.setLayout(self.hlayout)
        print self.hlayout.parent()

    def update_buttons(self):
        layout = self.hlayout.takeAt(1)
        for button in self.property_buttons:
            button.hide()
            del button

        dynamic_hlayout = QHBoxLayout()

        self.property_buttons = []
        
        if self.last_checked_label != None:
            for key in self.label_properties[self.last_checked_label].keys():
                if key in ["type", "class"]:
                    continue
                vlayout = self.create_choice_list(key)
                buttongroup = QButtonGroup()
                for value in self.properties[key]:
                    button = self.create_button(value)
                    self.property_buttons.append(button)
                    vlayout.addWidget(button)
                    buttongroup.addButton(button)
                dynamic_hlayout.addLayout(vlayout)

        self.hlayout.addLayout(dynamic_hlayout)

    def add_label(self, label_name, properties = {}):
        self.label_names.append(label_name)
        self.label_properties[label_name] = properties
        for key, value in properties.iteritems():
            if self.properties.has_key(key):
                self.properties[key] |= set(value)
            else:
                self.properties[key] = set(value)

    def get_checked_label_button(self):
        return self.label_buttongroup.checkedButton()

    def create_choice_list(self, list_name, elements = []):
        vlayout = QVBoxLayout()
        vlayout.setSpacing(0)
        #vlayout.setMargin(0)
        #vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.addWidget(QLabel("<center><b>" + list_name + "</b></center>"))
        if len(elements) > 0:
            buttongroup = QButtonGroup()
            for element in elements:
                self.create_button(element)
        return vlayout

    def clickedButton(self):
        button = self.get_checked_label_button()
        label_name = str(button.text())
        print label_name

    def clickedLabelButton(self):
        button = self.get_checked_label_button()
        label_name = str(button.text())
        if label_name != self.last_checked_label:
            print label_name, self.last_checked_label
            self.last_checked_label = label_name
            self.update_buttons()

    def load(self, config_filepath):
        execfile(config_filepath)
        #if self.get_checked_label_button() == None:
        #    if len(self.label_buttongroup.buttons()) != 0:
        #        self.label_buttongroup.buttons()[0].setChecked(True)
        #        
        #self.last_checked_label = str(self.get_checked_label_button().text())
        self.update_label_buttons()
        self.update_buttons()
        
def main():
    app = QApplication(sys.argv)

    ba = ButtonArea()
    ba.load("example_config.py")
    ba.show()

    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())

