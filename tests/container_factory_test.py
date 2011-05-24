from sloth.annotations.container import *

class MockupContainer:
    pass

def test_import_callable():
    containers = (('*', 'container_factory_test.MockupContainer'),)
    factory = AnnotationContainerFactory(containers)
    item = factory.create('test')
    assert isinstance(item, MockupContainer)

