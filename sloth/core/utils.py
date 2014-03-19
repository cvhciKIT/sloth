import importlib
from sloth.core import exceptions


def import_callable(module_path_name):
    """
    Import the callable given by ``module_path_name``.
    """
    try:
        module_path, name = module_path_name.rsplit('.', 1)
    except ValueError:
        raise exceptions.ImproperlyConfigured('%s is not a valid module path' % module_path_name)
    try:
        mod = importlib.import_module(module_path)
    except ImportError as e:
        raise exceptions.ImproperlyConfigured('Error importing module %s: "%s"' % (module_path, e))
    try:
        item_callable = getattr(mod, name)
    except AttributeError:
        raise exceptions.ImproperlyConfigured('Module "%s" does not define a "%s" callable' % (module_path, name))

    return item_callable
