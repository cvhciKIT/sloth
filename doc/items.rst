.. highlight:: python

=====
Items
=====

Visualization items are reponsible for bringing the labels to the users screen. The
visualization in the label tool is object based, i.e. for each label the label
tool creates a item object that is responsible for drawing the label.

Predefined items
================

The label tool comes with a few predefined visualization items:

- ``items.PointItem``

    Draws a point.  Expects the label to have keys ``x`` and ``y`` with the coordinates as values.

- ``items.RectItem``

    Draws a rectangle.  Expects the label to have keys ``x``, ``y``, ``width`` and ``height``.

- ``items.PolygonItem``

    Draws a polygon.  Expects the label to have keys ``xn`` and ``yn``, which are ``;``-separated
    lists of point coordinates.

- ``items.IDRectItem``

    Extends ``RectItem``. Displays the value of ``id`` within the rectangle as text.
    When an item is selected, the hotkey ``i`` can be used to cycle between numerical id values.

- ``items.OccludablePointItem``

    Extends ``PointItems``. Draws the point in a different color (red) when the value of ``occluded`` is ``True``.
    The hotkey ``o`` is defined to toggle the ``occluded`` property.

The predefined items can be used in different ways.  If you specify the class name in
the configuration, the constructor will be called for initializing the item.  However,
you can also create and instance of the item, configure for example the color, and then
use this instance in the configuration.  The predefined items have their ``__call__`` operator
overloaded and will function as a factory creating new items similar to the current instance.
You can make use of this in the configuration to for example specify the color of the
created rectangles, maybe even different kinds for different label types::

    # this your custom configuration module
    from PyQt4.Qt import *

    RedRectItem = items.RectItem()
    RedRectItem.setColor(Qt.red)
    GreenRectItem = items.RectItem()
    GreenRectItem.setColor(Qt.green)

    ITEMS = {
        "rect" : RedRectItem,
        "head" : GreenRectItem,
    }

items.RectItem
==============

Usage:

  * Can be moved by Left/Right/Up/Down keys.  If Shift is pressed, step is increased.  If Control is pressed,
    width and height are modified instead of position.

.. _CUSTOM_ITEMS:

Write your own visualization item
=================================

The base class for all visualization item is the :ref:`BaseItem <BaseItem>` class.  In
order to write a new visualization item, you need to subclass this class and implement
a few functions.

The easiest way to visualize your label is by using some of the existing Qt graphics items.  You can initialize
it in the constructor and be done::

    class MyRectItem(BaseItem):
        def __init__(self, index, data):
            # Call the base class constructor.  This will make the label
            # data available in self.data
            BaseItem.__init__(self, index, data)

            # Create a new rect item and add it as child item. 
            # This defines what will be displayed for this label, since the
            # BaseItem base class itself does not display anything.
            x, y, width, height = map(float, (self.data['x'],     self.data['y'],
                                              self.data['width'], self.data['height']))
            self.rect_ = QGraphicsRectItem(x, y, width, height, self)

For advanced usage, for example allowing the label to be moved by the mouse, we need to
do some more.  First, we need to allow the item to be selectable and movable.  In the constructor
set the graphics items flags to allow interactive modfications of the item::

    self.setFlags(QGraphicsItem.ItemIsSelectable | \
                  QGraphicsItem.ItemIsMovable | \
                  QGraphicsItem.ItemSendsGeometryChanges | \
                  QGraphicsItem.ItemSendsScenePositionChanges)

By overriding ``ìtemChange`` we get notified about item changes, such as a position change. Especially, we need
to inform the model about the modification::

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            self.updateModel()
        return AnnotationGraphicsItem.itemChange(self, change, value)

    def updateModel(self):
        rect = QRectF(self.scenePos(), self.rect_.size())
        self.data['x']      = rect.topLeft().x()
        self.data['y']      = rect.topLeft().y()
        self.data['width']  = float(rect.width())
        self.data['height'] = float(rect.height())

        self.index().model().setData(self.index(), QVariant(self.data), DataRole)

For even more advanced usage, such as drawing your own shapes, catching keys etc., please consult
Qt's `QGraphicsItem documentation`_.

.. _QGraphicsItem documentation: http://doc.trolltech.com/latest/qgraphicsitem.html

Factorize your custom visualization item
========================================

The predefined items are implemented in such a way so that they can be used as template
to create new, similar items.  In order to implement something similar for your own
visualization items, you need to overload your classes ``__call__`` operator and
return a new visualization item with all properties cloned that you would like
to clone.

Example::

    class MyRectItem(BaseItem):
        def __init__(self, index, data):
            BaseItem.__init__(self, index, data)
            self.color_ = Qt.red

        def setColor(self, color):
            self.color_ = color

        def __call__(self, index, data):
            newitem = MyRectItem(index, data)
            newitem.setColor(self.color_)
            return newitem

You can see that the ``__call__`` operator takes the same arguments as the constructor.
In its implementation it first creates a new visualization item, and then sets the
color to the same as its own before returning the new item.

