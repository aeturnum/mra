import json

_default_file = 'settings.json'

class SettingsError(Exception):
    pass

class Settings(object):
    @staticmethod
    def load_from_file(path=None):
        if path is None:
            global _default_file
            path = f'./{_default_file}'

        settings_data = json.load(open(path))
        return Settings(settings_data)

    def __init__(self, data = None):
        """

        :param dict valid_keys:
        """
        self._registry = {}
        if not data:
            data = {}

        for key, value in data.item():
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