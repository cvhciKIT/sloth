import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from sloth.gui.floatinglayout import FloatingLayout
import logging

LOG = logging.getLogger(__name__)


def unique_list(seq):
    seen = {}
    result = []
    for item in seq:
        if item in seen:
            continue
        seen[item] = 1
        result.append(item)
    return result


class ButtonListWidget(QGroupBox):
    selectionChanged = pyqtSignal(object)

    def __init__(self, name, parent=None):
        QGroupBox.__init__(self, name, parent)
        self.setLayout(FloatingLayout())

        self.name = name
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(False)
        self.buttons = {}

    def create_button(self, button_name):
        button = QPushButton(button_name)
        button.setFlat(True)
        button.setCheckable(True)
        button.clicked.connect(self.clickedButton)
        return button

    def add_button(self, button_name):
        button = self.create_button(button_name)
        self.buttons[button_name] = button
        self.layout().addWidget(button)
        self.button_group.addButton(button)
        return button

    def get_button(self, button_name):
        return self.buttons[button_name]

    def toggleChecked(self, button_name, apply=True):
        selection = None

        for button in self.button_group.buttons():
            if button.text() != button_name:
                button.setChecked(False)
            else:
                if apply:
                    button.setChecked(not button.isChecked())
                if button.isChecked():
                    selection = button_name

        self.selectionChanged.emit(selection)

    def clickedButton(self):
        button_name = str(self.sender().text())
        self.toggleChecked(button_name, False)

        #for button in self.button_group.buttons():
            #if button is not self.sender():
                #button.setChecked(False)
        #print "sender:", label_name

    def get_checked_button(self):
        return self.button_group.checkedButton()


class ButtonArea(QWidget):
    stateChanged = pyqtSignal(object)

    def __init__(self, labels=None, parent=None):
        QWidget.__init__(self, parent)

        self.label_names = []
        self.label_properties = {}

        self.properties = {}
        self.property_buttons = []

        self.label_button_list = ButtonListWidget("Labels")
        self.property_button_lists = {}

        self.hotkeys = []

        self.vlayout = QVBoxLayout()
        self.vlayout.setAlignment(Qt.AlignTop)
        self.vlayout.addWidget(self.label_button_list)
        self.stateChanged.connect(self.stateHasChanged)

        if labels is not None:
            for label in labels:
                # Description is given in key 'text'.
                # If empty, use the type attribute.
                name = label.get('name', '') or label.get('attributes', {}).get('type', '') 
                self.add_label(name, label.get('attributes', {}))

        self.init_button_lists()
        self.vlayout.addStretch(1)
        self.setLayout(self.vlayout)

    def stateHasChanged(self, state):
        LOG.debug("stateChanged(object) %s", state)

    def init_button_lists(self):
        for label_name in self.label_names:
            button = self.label_button_list.add_button(label_name)
        self.label_button_list.selectionChanged.connect(self.clickedLabelButton)

        for key, property_values in self.properties.items():
            if key in ["type", "class"]:
                continue
            button_list = ButtonListWidget(key)
            for value in property_values:
                button = button_list.add_button(value)
                #button.clicked.connect(self.clickedButton)
            button_list.selectionChanged.connect(self.clickedButton)

            button_list.hide()
            LOG.debug(key)
            self.property_button_lists[key] = button_list
            self.vlayout.addWidget(button_list)

        for choice, name, hotkey in self.hotkeys:
            if choice == "" or choice is None:
                button = self.label_button_list.get_button(name)
                shortcut = QShortcut(QKeySequence(hotkey), button, button.click)
            else:
                button = self.property_button_lists[choice].get_button(name)
                shortcut = QShortcut(QKeySequence(hotkey), button, button.click)
            button.setToolTip("[" + str(hotkey) + "]")

    def show_only_label_properties(self, label_name):
        for name, button_list in self.property_button_lists.items():
            if label_name in self.label_properties and name in self.label_properties[label_name].keys():
                button_list.show()
            else:
                button_list.hide()

    def add_label(self, label_name, properties=None):
        self.label_names.append(label_name)
        self.label_properties[label_name] = properties or {}
        for key, value in properties.items():
            if key in self.properties:
                self.properties[key] = unique_list(self.properties[key] + value)

            else:
                self.properties[key] = value

    def get_checked_label_button(self):
        return self.label_button_list.get_checked_button()

    def add_hotkey(self, choice, name, hotkey):
        self.hotkeys.append((choice, name, hotkey))

    def get_current_state(self):
        label_button = self.get_checked_label_button()
        if label_button != None:
            result = {}
            label = str(label_button.text())
            if label in self.label_properties:
                if "type" in self.label_properties[label]:
                    result["type"] = self.label_properties[label]["type"]
                if "class" in self.label_properties[label]:
                    result["class"] = self.label_properties[label]["class"]
                for name, button_list in self.property_button_lists.items():
                    if button_list.isVisible():
                        checked_button = button_list.get_checked_button()
                        if checked_button != None:
                            result[button_list.name] = str(checked_button.text())
            return result

        return None

    def clickedButton(self, newselection):
        LOG.debug("selectionChanged: %s" % newselection)
        self.stateChanged.emit(self.get_current_state())

    def clickedLabelButton(self, label_name):
        #button = self.get_checked_label_button()
        #print button
        if label_name is not None:
            LOG.debug("ButtonArea: %s" % label_name)
            self.show_only_label_properties(label_name)
        else:
            LOG.debug("Selection Mode")
            self.show_only_label_properties("")
        self.stateChanged.emit(self.get_current_state())

    def exitInsertMode(self):
        button = self.label_button_list.get_checked_button()
        if button is not None:
            self.label_button_list.toggleChecked(button)


def main():
    from conf import config

    config.update("example_config")

    app = QApplication(sys.argv)
    ba = ButtonArea(config.LABELS, config.HOTKEYS)
    ba.show()

    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())

