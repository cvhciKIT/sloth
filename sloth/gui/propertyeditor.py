from sloth.core.exceptions import ImproperlyConfigured
from sloth.annotations.model import AnnotationModelItem
from sloth.gui.floatinglayout import FloatingLayout
from sloth.utils.bind import bind
import sys
from PyQt4.QtCore import pyqtSignal, QSize, Qt
from PyQt4.QtGui import QApplication, QWidget, QGroupBox, QVBoxLayout, QPushButton, QButtonGroup, QScrollArea
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

class LabelEditor(QScrollArea):
    def __init__(self, items, parent=None):
        QScrollArea.__init__(self, parent)
        self._content = QWidget()
        self._editor = parent
        self._items = items

        # Find all classes
        self._label_classes = set([item.get('class', item['type']) for item in items])
        n_classes = len(self._label_classes)
        LOG.debug("Creating editor for %d item classes: %s" % (n_classes, ", ".join(list(self._label_classes))))

        # Widget layout
        self._layout = QVBoxLayout()
        self._content.setLayout(self._layout)
        self._boxes   = {}
        self._layouts = {}
        self._buttons = {}

        if n_classes == 0:
            pass
        elif n_classes == 1:
            # Just display all properties
            lc = self._label_classes.copy().pop()
            for attr in self._editor.getLabelClassAttributes(lc):
                if attr == 'class' or attr == 'type': continue
                self.addAttributeEditor(item, lc, attr, self._editor.getLabelClassAttributeChoices(lc, attr))
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

    def onButtonClicked(self, attr, val):
        LOG.debug("Button %s: %s clicked" % (attr, val))
        button = self._buttons[attr][val]

        # Unpress all other buttons
        for v, but in self._buttons[attr].items():
            if but is not button:
                but.setChecked(False)

        # Update model item
        for item in self._items:
            if button.isChecked():
                item[attr] = val
            else:
                item[attr] = None

    def addAttributeEditor(self, item, lc, attr, vals):
        box = QGroupBox(attr, self)
        layout = FloatingLayout()
        box.setLayout(layout)
        self._boxes[attr] = box
        self._layouts[attr] = layout
        self._buttons[attr] = {}
        for v in vals:
            button = QPushButton(v, box)
            button.setFlat(True)
            button.setCheckable(True)
            button.setChecked(attr in item and item[attr] == v)
            self._buttons[attr][v] = button
            layout.addWidget(button)
            button.clicked.connect(bind(self.onButtonClicked, attr, v))
        self._layout.addWidget(box)

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
        self._class_config  = {}
        self._class_items   = {}

        self._setupGUI()

        # Add label classes from config
        for label in config:
            self.addLabelClass(label)

    def addLabelClass(self, label_config):
        # Check label configuration
        if 'attributes' not in label_config:
            raise ImproperlyConfigured("Label with no 'attributes' dict found")
        attrs = label_config['attributes']
        if 'type' not in attrs:
            raise ImproperlyConfigured("Labels must have an attribute 'type'")
        # TODO: Maybe don't do this?
        if 'class' not in attrs:
            attrs['class'] = attrs['type']
        label_class = attrs['class']
        if label_class in self._class_config:
            raise ImproperlyConfigured("Label with class '%s' defined more than once" % label_class)

        # Store config
        # TODO: Handle special properties
        self._class_config[label_class] = label_config

        # Add dummy item for insertion
        # TODO: Put stuff into dict first
        self._class_items[label_class]  = AnnotationModelItem(label_config['attributes'])

        # Add label class button
        button = QPushButton(label_class, self)
        button.setCheckable(True)
        button.setFlat(True)
        button.clicked.connect(self.onClassButtonPressed)
        self._class_buttons[label_class] = button
        self._classbox_layout.addWidget(button)

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


