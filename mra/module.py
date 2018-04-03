from asyncio import Lock

# global registry
Registry = {}
Registry_Lock = Lock()

class DynamicModule(object):
    PATH = "Global"

    def __init__(self):
        self.settings = {}

    @staticmethod
    async def _global_register(path, module):
        global Registry
        global Registry_Lock
        with yield from Registry_Lock:
            if path in Registry:
                raise Exception(
                    f"Can't register {module}. Path {path} is already registered to module {Registry[path]}!"
                )

    @staticmethod
    def create(path, settings):
        global Registry
        obj = Registry[path]()
        obj.load_settings(settings)
        return obj

    @classmethod
    def register(cls):
        DynamicModule._global_register(cls.PATH, cls.__class__)

    @classmethod
    def load_settings(self, settings_dict):
        self.settings = settings_dict[self.PATH]




