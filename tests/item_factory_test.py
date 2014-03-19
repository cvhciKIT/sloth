import pytest
from sloth.items import Factory


class MockupRectItem:
    pass


class MockupPointItem:
    pass


class MockupPolygonItem:
    pass


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