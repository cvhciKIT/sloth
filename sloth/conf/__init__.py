from conf import default_config
import importlib

class Config:
    def __init__(self):
        # init the configuration with the default config
        for setting in dir(default_config):
            if setting == setting.upper():
                setattr(self, setting, getattr(default_config, setting))

    def update(self, module_path):
        try:
            mod = importlib.import_module(module_path)
        except ImportError, e:
            raise ImportError("Could not import configuration '%s' (Is it on sys.path?): %s" % (module_path, e))

        for setting in dir(mod):
            if setting == setting.upper():
                setting_value = getattr(mod, setting)
                setattr(self, setting, setting_value)

config = Config()

