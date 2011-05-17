from sloth.core import exceptions
import importlib

class Factory:
    """
    A generic factory for both items and inserters.
    """

    def __init__(self, items=None):
        """
        Constructor.

        Parameters
        ==========
        items: dict
            Mapping from type to python callable.  If not None, all mappings
            will be registered with the factory.
        """
        self.items_ = {}

        if items is not None:
            for _type, item in items.iteritems():
                self.register(_type, item, replace=True)

    def import_callable(self, module_path_name):
        """
        Import the callable given by ``module_path_name``.
        """
        try:
            module_path, name = module_path_name.rsplit('.', 1)
        except ValueError:
            raise exceptions.ImproperlyConfigured('%s is not a valid module path' % module_path_name)
        try:
            mod = importlib.import_module(module_path)
        except ImportError, e:
            raise exceptions.ImproperlyConfigured('Error importing module %s: "%s"' % (module_path, e))
        try:
            item_callable = getattr(mod, name)
        except AttributeError:
            raise exceptions.ImproperlyConfigured('Module "%s" does not define a "%s" callable' % (module_path, name))

        return item_callable

    def register(self, _type, item, replace=False):
        """
        Register a new type-item mapping.

        Parameters
        ==========
        _type: string
            Type of the item.
        item: python callable or string
            Reference to the callable which creates the new object.
        """
        _type = _type.lower()

        if _type in self.items_ and not replace:
            raise Exception("Type %s already has an item: %s" % \
                             (_type, str(self.items_[_type])))
        else:
            if type(item) == str:
                item = self.import_callable(item)
            self.items_[_type] = item

    def clear(self, _type=None):
        """
        Remove a type-item mapping.

        Parameters
        ==========
        _type: str
            Type for which the mapping should be removed.  If None, all
            mappings will be removed.
        """
        if _type is None:
            self.items_     = {}
        else:
            _type = _type.lower()
            if _type in self.items_:
                del self.items_[_type]

    def create(self, _type, *args, **kwargs):
        """
        Create a new object.

        Parameters
        ==========
        _type: str
            Type for which a new object should be created.

        All further arguments will be passed to the constructor/creating function
        of the mapping.

        Returns
        =======
        Newly created object. If for the given type no mapping exists, this
        function returns ``None``.
        """
        _type = _type.lower()

        if _type not in self.items_:
            return None
        item = self.items_[_type]
        if item is None:
            return None
        return item(*args, **kwargs)

### testing
import pytest
class MockupRectItem:    pass
class MockupPointItem:   pass
class MockupPolygonItem: pass

def _create_factory():
    itemfactory = Factory({'point':   MockupPointItem,
                           'polygon': MockupPolygonItem})
    itemfactory.register('rect', MockupRectItem)

    return itemfactory

def test_register():
    itemfactory = _create_factory()

    item = itemfactory.create('rect')
    assert isinstance(item, MockupRectItem)
    item = itemfactory.create('point')
    assert isinstance(item, MockupPointItem)
    item = itemfactory.create('polygon')
    assert isinstance(item, MockupPolygonItem)
    item = itemfactory.create('polygon2')
    assert item is None

def test_register_fail():
    itemfactory = _create_factory()
    with pytest.raises(Exception):
        itemfactory.register('rect', MockupRectItem)

def test_register_replace():
    itemfactory = _create_factory()

    itemfactory.register('rect', MockupPolygonItem, replace=True)
    item = itemfactory.create('rect')
    assert isinstance(item, MockupPolygonItem)

def test_clear():
    itemfactory = _create_factory()

    item = itemfactory.create('rect')
    assert isinstance(item, MockupRectItem)
    itemfactory.clear('rect')
    item = itemfactory.create('rect')
    assert item is None

    item = itemfactory.create('point')
    assert isinstance(item, MockupPointItem)
    item = itemfactory.create('polygon')
    assert isinstance(item, MockupPolygonItem)
    itemfactory.clear()
    assert itemfactory.create('point') is None
    assert itemfactory.create('polygon') is None

