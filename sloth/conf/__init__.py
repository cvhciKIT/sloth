import os
import sys
import importlib
from sloth.conf import default_config


class Config:
    def __init__(self):
        # init the configuration with the default config
        for setting in dir(default_config):
            if setting == setting.upper():
                setattr(self, setting, getattr(default_config, setting))

    def update(self, module_path):
        try:
            oldpath = sys.path
            module_path = os.path.abspath(module_path)
            if module_path.endswith('.py'):
                module_path = module_path[:-3]
            module_dir, module_name = os.path.split(module_path)
            sys.path = [module_dir, ] + sys.path
            mod = importlib.import_module(module_name)
        except ImportError as e:
            raise ImportError("Could not import configuration '%s' (Is it on sys.path?): %s" % (module_path, e))
        finally:
            sys.path = oldpath

        for setting in dir(mod):
            if setting == setting.upper():
                setting_value = getattr(mod, setting)
                setattr(self, setting, setting_value)

config = Config()

