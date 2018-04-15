from mra.util import load_json
from mra.logger import Logger

_default_file = './settings.json'

class SettingsError(Exception):
    pass

class Settings(Logger):
    @staticmethod
    def load_from_file(path=None):
        if path is None:
            global _default_file
            path = _default_file

        settings_data = load_json(open(path).read())
        return Settings(settings_data, path)

    def __init__(self, data = None, path=None):
        """

        :param dict valid_keys:
        """
        super().__init__()
        self.path = path
        self._registry = {}
        if not data:
            data = {}

        for key, value in data.items():
            if type(value) is dict:
                value = Settings(value)
            self._registry[key] = value

    def __getitem__(self, item):
        """

        :param str item:
        :return:
        """
        # if self._valid_keys is not None and item not in self._valid_keys:
        #     raise ValueError(f"Key {item} is not a valid setting.")
        return self._registry.get(item, None)

    def __setitem__(self, key, value):
        """

        :param str key:
        :param any value:
        :return:
        """
        raise ValueError("Setting values of settings not allowed.")

    def get(self, key, default=None):
        return self._registry.get(key, default)

    def __contains__(self, item):
        return item in self._registry

    def add_sub_setting(self, key, data=None):
        """

        :param str key:
        :param list[str] keys:
        :return:
        """
        self._registry[key] = Settings(data)

