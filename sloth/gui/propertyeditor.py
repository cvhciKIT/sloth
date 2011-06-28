from sloth.core.exceptions import ImproperlyConfigured
from sloth.annotations.model import AnnotationModelItem
from sloth.gui.floatinglayout import FloatingLayout
from sloth.utils.bind import bind
import sys
from PyQt4.QtCore import pyqtSignal, QSize, Qt
from PyQt4.QtGui import QApplication, QWidget, QGroupBox, QVBoxLayout, QPushButton, QScrollArea
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

class AttributeHandlerFactory:
    def create(self, attribute, values):
        # At the moment we always create a DefaultAttributeHandler
        # But in the future this could also create user-defined attribute editors
        return DefaultAttributeHandler(attribute, values)

class AbstractAttributeHandler:
    def defaults(self):
        pass
    def updateValues(self, values):
        pass
    def setItems(self, items):
        pass

class DefaultAttributeHandler(QGroupBox, AbstractAttributeHandler):
    def __init__(self, attribute, values, parent=None):
        QGroupBox.__init__(self, attribute, parent)
        self._attribute     = attribute
        self._values        = []
        self._current_items = []
        self._defaults      = {}

        # Setup GUI
        self._layout = FloatingLayout()
        self.setLayout(self._layout)
        self._buttons = {}

        # Add interface elements
        self.updateValues(values)

    def updateValues(self, values):
        # TODO: Properly parse
        for val in values:
            if val not in self._values:
                self.addValue(val)

    def defaults(self):
        return self._defaults

    def addValue(self, v):
        button = QPushButton(v, self)
        button.setFlat(True)
        button.setCheckable(True)
        self._buttons[v] = button
        self._layout.addWidget(button)
        button.clicked.connect(bind(self.onButtonClicked, v))

    def reset(self):
        self._current_items = []
        for v, button in self._buttons.items():
            button.setChecked(False)
            button.setFlat(True)

    def setItems(self, items):
        self.reset()
        selected_values = set([item[self._attribute] for item in items if self._attribute in item])
        for val in selected_values:
            if len(selected_values) > 1:
                self._buttons[val].setFlat(False)
            else:
                self._buttons[val].setChecked(True)
        self._current_items = items

    def onButtonClicked(self, val):
        attr = self._attribute
        LOG.debug("Button %s: %s clicked" % (attr, val))
        button = self._buttons[val]

        # Unpress all other buttons
        for v, but in self._buttons.items():
            but.setFlat(True)
            if but is not button:
                but.setChecked(False)

        # Update model item
        for item in self._current_items:
            if button.isChecked():
                item[attr] = val
            else:
                item[attr] = None

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

        if n_classes == 0:
            pass
        elif n_classes == 1:
            # Just display all properties
            lc = self._label_classes.copy().pop()
            for attr in self._editor.getLabelClassAttributes(lc):
                if attr == 'class': continue
                handler = self._editor.getHandler(attr)
                handler.setItems(items)
                self._layout.addWidget(handler)
        else:
            # TODO
            # Find common properties of all classes
            properties = None
            for c in self._label_classes:
                if properties is None:
                    properties  = set(self._editor.getLabelClassAttributes(c))
                else:
                    properties &= set(self._editor.getLabelClassAttributes(c))

            # TODO: Remove properties with per-class value lists if more than one class selected
            # TODO: Order this somehow

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

        # Create attribute handler widgets or update their values
        for attr, vals in attrs.items():
            if attr == 'class': continue
            if attr in self._attribute_handlers:
                self._attribute_handlers[attr].updateValues(vals)
            else:
                self._attribute_handlers[attr] = self._handler_factory.create(attr, vals)

        # Add prototype item for insertion
        self._class_items[label_class] = AnnotationModelItem({ 'class': label_class })
        for attr in attrs:
            if attr == 'class': continue
            self._class_items[label_class].update(self._attribute_handlers[attr].defaults())

    def getHandler(self, attribute):
        return self._attribute_handlers[attribute]

    def getLabelClassAttributes(self, label_class):
        return self._class_config[label_class]['attributes']

    def getLabelClassAttributeChoices(self, label_class, attribute):
        return self._class_config[label_class]['attributes'][attribute]

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


