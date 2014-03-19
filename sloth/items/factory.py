from sloth.core.utils import import_callable


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
        self._items = {}

        if items is not None:
            for _type, item in items.items():
                self.register(_type, item, replace=True)

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
        _type = str(_type)
        if _type in self._items and not replace:
            raise Exception("Type %s already has an item: %s" %
                            (_type, str(self._items[_type])))
        else:
            if type(item) == str:
                item = import_callable(item)
            self._items[_type] = item

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
            self._items = {}
        else:
            _type = str(_type)
            if _type in self._items:
                del self._items[_type]

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
        _type = str(_type)
        if _type not in self._items:
            return None
        item = self._items[_type]
        if item is None:
            return None
        return item(*args, **kwargs)
