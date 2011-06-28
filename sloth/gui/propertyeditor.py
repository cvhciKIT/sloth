from sloth.core.exceptions import ImproperlyConfigured
from sloth.annotations.model import AnnotationModelItem
from sloth.gui.floatinglayout import FloatingLayout
from sloth.utils.bind import bind
import sys
from PyQt4.QtCore import pyqtSignal, QSize, Qt
from PyQt4.QtGui import QApplication, QWidget, QGroupBox, QVBoxLayout, QPushButton, QScrollArea, QLineEdit, QDoubleValidator, QIntValidator
import logging
LOG = logging.getLogger(__name__)

# This is really really ugly, but the QDockWidget for some reason does not notice when
# its child widget becomes smaller...
# Therefore we manually set its minimum size when our own minimum size changes
class MyVBoxLayout(QVBoxLayout):
    def __init__(self, parent=None):
        QVBoxLayout.__init__(self, parent)
        self._last_size = QSize(0, 0)

    def setGeometry(self, r):
        QVBoxLayout.setGeometry(self, r)
        try:
            wid = self.parentWidget().parentWidget()

            new_size = self.minimumSize()
            if new_size == self._last_size: return
            self._last_size = new_size

            twid = wid.titleBarWidget()
            if twid is not None:
                theight = twid.sizeHint().height()
            else:
                theight = 0

            new_size += QSize(0, theight)
            wid.setMinimumSize(new_size)

        except Exception:
            pass

class AbstractAttributeHandler:
    def defaults(self):
        pass
    def updateValues(self, values):
        pass
    def setItems(self, items, showItemClasses=False):
        pass

class AttributeHandlerFactory:
    def create(self, attribute, values):
        # At the moment we always create a DefaultAttributeHandler
        # But in the future this could also create user-defined attribute editors

        # Class attribute cannot be changed
        if attribute == 'class':
            return None

        # Just a value. No attribute editor needed, we just add it to the item to be inserted...
        if isinstance(values, str) or isinstance(values, float) or isinstance(values, int):
            return None
        # If it's already a handler, just return it
        elif isinstance(values, AbstractAttributeHandler):
            return values
        # Else, we create our own default handler
        else:
            return DefaultAttributeHandler(attribute, values)

class DefaultAttributeHandler(QGroupBox, AbstractAttributeHandler):
    def __init__(self, attribute, values, parent=None):
        QGroupBox.__init__(self, attribute, parent)
        self._attribute      = attribute
        self._values         = []
        self._current_items  = []
        self._defaults       = {}
        self._inputField     = None
        self._inputFieldType = None
        self._insertIndex    = -1

        # Setup GUI
        self._layout = FloatingLayout()
        self.setLayout(self._layout)
        self._buttons = {}

        # Add interface elements
        self.updateValues(values)

    def updateValues(self, values):
        if isinstance(values, type):
            self.addInputField(values)
        else:
            for val in values:
                if isinstance(val, type):
                    self.addInputField(val)
                elif val == "*":
                    self._insertIndex = self._layout.count()
                else:
                    if val not in self._values:
                        self.addValue(val)

    def defaults(self):
        return self._defaults

    def onInputFieldReturnPressed(self):
        val = str(self._inputField.text())
        if self._insertIndex >= 0 and val not in self._buttons:
            self.addValue(val, self._insertIndex)
        for item in self._current_items:
            item[self._attribute] = val
        self.updateButtons()
        self.updateInputField()

    def addInputField(self, _type):
        if self._inputField is None:
            self._inputFieldType = _type
            self._inputField = QLineEdit()
            if _type is float:
                self._inputField.setValidator(QDoubleValidator())
            elif _type is int:
                self._inputField.setValidator(QIntValidator())

            self._layout.addWidget(self._inputField)
            self._inputField.returnPressed.connect(self.onInputFieldReturnPressed)
        elif self._inputFieldType is not _type:
            raise ImproperlyConfigured("Input field for attribute '%s' configured twice with different types %s != %s"\
                    % (self._attribute, self._inputFieldType, _type))

    def addValue(self, v, pos=-1):
        self._values.append(v)
        button = QPushButton(v, self)
        button.setFlat(True)
        button.setCheckable(True)
        self._buttons[v] = button
        # TODO: Add at proper position
        if pos == -1:
            self._layout.addWidget(button)
        else:
            self._layout.insertWidget(pos, button)
        button.clicked.connect(bind(self.onButtonClicked, v))

    def reset(self):
        self._current_items = []
        for v, button in self._buttons.items():
            button.setChecked(False)
            button.setFlat(True)

    def getSelectedValues(self):
        return set([str(item[self._attribute]) for item in self._current_items if self._attribute in item and item[self._attribute] is not None])

    def updateInputField(self):
        if self._inputField is not None:
            self._inputField.clear()
            selected_values = self.getSelectedValues()
            if len(selected_values) > 1:
                self._inputField.setPlaceholderText(", ".join(selected_values))
            elif len(selected_values) == 1:
                self._inputField.setText(iter(selected_values).next())

    def updateButtons(self):
        selected_values = self.getSelectedValues()
        for val, button in self._buttons.items():
            if val in selected_values:
                if len(selected_values) > 1:
                    button.setFlat(False)
                    button.setChecked(False)
                else:
                    button.setFlat(True)
                    button.setChecked(True)
            else:
                button.setFlat(True)
                button.setChecked(False)

    def setItems(self, items, showItemClasses=False):
        self.reset()
        if showItemClasses:
            title = ", ".join(set([item['class'] for item in items]))
            self.setTitle(self._attribute + " (" + title + ")")
        else:
            self.setTitle(self._attribute)

        self._current_items = items

        self.updateButtons()
        self.updateInputField()

    def onButtonClicked(self, val):
        attr = self._attribute
        LOG.debug("Button %s: %s clicked" % (attr, val))
        button = self._buttons[val]

        # Update model item
        for item in self._current_items:
            if button.isChecked():
                item[attr] = val
            else:
                item[attr] = None

        # Unpress all other buttons
        for v, but in self._buttons.items():
            but.setFlat(True)
            if but is not button:
                but.setChecked(False)

        # Update input field
        self.updateInputField()


class LabelEditor(QScrollArea):
    def __init__(self, items, parent=None):
        QScrollArea.__init__(self, parent)
        self._editor = parent
        self._items = items

        # Find all classes
        self._label_classes = set([item['class'] for item in items if 'class' in item])
        n_classes = len(self._label_classes)
        LOG.debug("Creating editor for %d item classes: %s" % (n_classes, ", ".join(list(self._label_classes))))

        # Widget layout
        self._layout = QVBoxLayout()
        self._content = QWidget()
        self._content.setLayout(self._layout)

        attributes = set()
        for lc in self._label_classes:
            attributes |= set(self._editor.getLabelClassAttributes(lc))

        for attr in attributes:
            handler = self._editor.getHandler(attr)
            if handler is not None:
                if len(items) > 1:
                    valid_items = [item for item in items if attr in self._editor.getLabelClassAttributes(item['class'])]
                    handler.setItems(valid_items, True)
                else:
                    handler.setItems(items)
                self._layout.addWidget(handler)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(self._content)

    def sizeHint(self):
        minsz = self.minimumSize()
        sz = self._layout.minimumSize()
        left, top, right, bottom = self.getContentsMargins()
        return QSize(max(minsz.width(), sz.width() + left + right), max(minsz.height(), sz.height() + top + bottom))

    def labelClasses(self):
        return self._label_classes

    def currentProperties(self):
        if len(self._items) > 1:
            return {}
        else:
            return self._items[0]

class PropertyEditor(QWidget):
    # Signals
    insertionModeStarted       = pyqtSignal(str)
    insertionModeEnded         = pyqtSignal()
    insertionPropertiesChanged = pyqtSignal(object)
    editPropertiesChanged      = pyqtSignal(object)

    def __init__(self, config, parent=None):
        QWidget.__init__(self, parent)
        self._class_config       = {}
        self._class_items        = {}
        self._class_prototypes   = {}
        self._attribute_handlers = {}
        self._handler_factory    = AttributeHandlerFactory()

        self._setupGUI()

        # Add label classes from config
        for label in config:
            self.addLabelClass(label)

    def addLabelClass(self, label_config):
        # Check label configuration
        if 'attributes' not in label_config:
            raise ImproperlyConfigured("Label with no 'attributes' dict found")
        attrs = label_config['attributes']
        if 'class' not in attrs:
            raise ImproperlyConfigured("Labels must have an attribute 'class'")
        label_class = attrs['class']
        if label_class in self._class_config:
            raise ImproperlyConfigured("Label with class '%s' defined more than once" % label_class)

        # Store config
        self._class_config[label_class] = label_config

        # Parse configuration and create handlers and item
        self.parseConfiguration(label_class, label_config)

        # Add label class button
        button = QPushButton(label_class, self)
        button.setCheckable(True)
        button.setFlat(True)
        button.clicked.connect(self.onClassButtonPressed)
        self._class_buttons[label_class] = button
        self._classbox_layout.addWidget(button)

    def parseConfiguration(self, label_class, label_config):
        attrs = label_config['attributes']

        # Add prototype item for insertion
        self._class_items[label_class] = AnnotationModelItem({ 'class': label_class })

        # Create attribute handler widgets or update their values
        for attr, vals in attrs.items():
            if attr in self._attribute_handlers:
                self._attribute_handlers[attr].updateValues(vals)
            else:
                handler = self._handler_factory.create(attr, vals)
                if handler is None:
                    self._class_items[label_class][attr] = vals
                else:
                    self._attribute_handlers[attr] = handler

        for attr in attrs:
            if attr in self._attribute_handlers:
                self._class_items[label_class].update(self._attribute_handlers[attr].defaults())

    def getHandler(self, attribute):
        if attribute in self._attribute_handlers:
            return self._attribute_handlers[attribute]
        else:
            return None

    def getLabelClassAttributes(self, label_class):
        return self._class_config[label_class]['attributes'].keys()

    def onClassButtonPressed(self):
        if self.sender().isChecked():
            self.startInsertionMode(str(self.sender().text()))
        else:
            self.endInsertionMode()

    def startInsertionMode(self, label_class):
        self.endInsertionMode(False)
        for lc, button in self._class_buttons.items():
            button.setChecked(lc == label_class)
        LOG.debug("Starting insertion mode for %s" % label_class)
        self._label_editor = LabelEditor([self._class_items[label_class]], self)
        self._layout.insertWidget(1, self._label_editor, 0)
        self.insertionModeStarted.emit(label_class)

    def endInsertionMode(self, uncheck_buttons=True):
        if self._label_editor is not None:
            LOG.debug("Ending insertion mode")
            self._label_editor.hide()
            self._layout.removeWidget(self._label_editor)
            self._label_editor = None
            self.uncheckAllButtons()
            self.insertionModeEnded.emit()

    def uncheckAllButtons(self):
        for lc, button in self._class_buttons.items():
            button.setChecked(False)

    def markEditButtons(self, label_classes):
        for lc, button in self._class_buttons.items():
            button.setFlat(lc not in label_classes)

    def currentEditorProperties(self):
        if self._label_editor is None:
            return None
        else:
            return self._label_editor.currentProperties()

    def startEditMode(self, model_items):
        self.endInsertionMode()
        LOG.debug("Starting edit mode for items: %s" % model_items)
        self._label_editor = LabelEditor(model_items, self)
        self.markEditButtons(self._label_editor.labelClasses())
        self._layout.insertWidget(1, self._label_editor, 0)

    def _setupGUI(self):
        self._class_buttons = {}
        self._label_editor  = None

        # Label class buttons
        self._classbox = QGroupBox("Labels", self)
        self._classbox_layout = FloatingLayout()
        self._classbox.setLayout(self._classbox_layout)

        # Global widget
        self._layout = MyVBoxLayout()
        self.setLayout(self._layout)
        self._layout.addWidget(self._classbox, 0)
        self._layout.addStretch(1)

def main():
    from sloth.conf import config
    config.update("/home/mfischer/videmo_config_new_simple")

    app = QApplication(sys.argv)
    ba = PropertyEditor(config.LABELS)
    ba.show()

    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())


