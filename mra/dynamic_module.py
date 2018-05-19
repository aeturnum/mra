import importlib.util
import inspect
import multiprocessing
import os
import sys
from os.path import split, basename, join

from mra.helpers.logger import Logger
from mra.settings import Settings, SettingsError

# global registry
Registry = {}

# default location for actions
_DEFAULT_MODULE_ROOTS = (
    # package directory
    split(__file__)[0],
    os.getcwd()
)

# todo add testing files
# don't add this file
_BANNED_FILES = (
    __file__,
    '__main__.py' # banned for real
)

# Classes that we don't want added
# todo: find a better way of doing this
_BANNED_CLASSES = (
    'dynamic_module.DynamicModule',
    'action.Action',
    'resource_pool.ResourcePool'
)

_DEFAULT_PREFIXES = (
    ''
)

# this can probably be a *lot* lower
_DRY_RUN_TIMEOUT = 5

# modified at runtime

Prefixes = set()

class DynamicModuleManager(Logger):
    @staticmethod
    def _reset_registry():
        """
        Debug method for resetting the registry
        :return:
        """
        global Registry
        Registry = {}

    @staticmethod
    def _gather_file(path, test_process=False, logger=None):
        """

        :param str path: Path to python file
        :param bool test_process:  If true, this is hosted in a separate process and should not load modules
        :return:
        """
        if test_process:
            sys.stdout = open(os.devnull, 'w')
        global _BANNED_CLASSES

        # this must be called in a thread because if the module exec blocks, it must be killed
        module_name = basename(path).split(".")[0]

        # todo: parse module name
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except SyntaxError:
            if logger:
                logger.log_warn(f'File {path} contains a syntax log_error - skipping')
            # exit with a bad code if we're being called in a process
            if test_process:
                exit(1)
        except:
            # exit with a bad code if we're being called in a process
            if test_process:
                exit(1)
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and obj.__module__ == module_name and issubclass(obj, DynamicModule):
                full_name = f'{obj.__module__}.{name}'
                # this will be called in a process first to ensure the process works
                # Also check if this is a base class that won't ever been created
                # Also check if we've banned this class
                if logger:
                    logger.log_system(f"Checking if we want to load {obj}...")
                if not test_process and full_name not in _BANNED_CLASSES:
                    if logger:
                        logger.log_system(f"Loading {obj}")
                    obj.register(logger=logger)

    def gather(self, settings):
        """
        Gather all DynamicModules specified by settings
        :param settings:
        :return:
        """
        # todo: add a paranoid setting, on by default, that will crash if loading something fails
        global _DEFAULT_MODULE_ROOTS
        global _BANNED_FILES

        roots = []
        roots.extend(_DEFAULT_MODULE_ROOTS)
        roots.extend(settings.get('modules', []))
        self.log_system("Begining to gather modules from directories: {}", roots)
        for action_directory in roots:
            for dir_name, sub_dirs, file_list in os.walk(action_directory):
                for file_name in file_list:
                    # open non-special python files
                    if file_name.endswith(".py") and not file_name.startswith('__'):
                        path = join(dir_name, file_name)
                        if path in _BANNED_FILES:
                            continue

                        self.log_system("Checking candidate file {}", file_name)
                        process = multiprocessing.Process(
                            target=DynamicModuleManager._gather_file,
                            args=(path, True)  # dry run
                        )
                        process.start()
                        # we run this in a seperate process first, because they can be killed, unlike
                        # python threads. This allows us to detect blocking python files.
                        process.join(timeout=_DRY_RUN_TIMEOUT)
                        if process.is_alive():
                            process.terminate()
                            process.join()
                            self.log_warn(f'File {path} did not terminate when loading module, probably blocks. Skipping.')
                        else:
                            if process.exitcode == 0:
                                # actually add the modules
                                # print(f'loading: {path}')
                                self.log_system(f'Loading file {path} into dynamic modules.')
                                DynamicModuleManager._gather_file(path, logger=self)
                            else:
                                print(f'File {path} has a non-zero exit code, indicating problems. Skipping.')

    def LoadClass(self, path):
        global Registry
        global _DEFAULT_PREFIXES
        global Prefixes
        paths = [f'{p}.{path}' for p in _DEFAULT_PREFIXES]
        paths.extend([f'{p}.{path}' for p in Prefixes])
        # make sure the litteral name is tried first
        # todo: this could be faster, but it's setup, which can be slow as hell
        self.log_system(f"Loading class from path '{path}'")
        paths.insert(0, path)
        for p in paths:
            self.log_spew(f"Checking possible sub-path '{p}'...")
            if p in Registry:
                self.log_system(f"Path '{p}' matches!")
                return Registry[p]

        raise SettingsError(f'Path {path} not found in global registry!')

    def CreateClass(self, path, args):
        return self.LoadClass(path)(*args)

    def __str__(self):
        return "DMM"

class DynamicModule(Logger):
    PATH = "Global"
    PREFIX = None
    SETTINGS_KEYS = []
    SETTINGS = None

    def __init__(self, reporter=False):
        super().__init__(reporter=reporter)
        self.settings = {}

    @staticmethod
    def _global_register(path, module, logger: Logger=None):
        global Registry
        global Prefixes
        if path in Registry:
            raise Exception(
                f"Can't register {module}. Path {path} is already registered to module {Registry[path]}!"
            )
        Registry[path] = module
        if module.PREFIX is not None:
            Prefixes.add(module.PREFIX)
        if logger:
            logger.log_debug(f'Added {module} under path "{path}"')

    # todo: maybe delete this?
    @staticmethod
    def create(path, settings, logger=None):
        global Registry
        obj = Registry[path]()
        obj.load_settings(settings)
        return obj

    @classmethod
    def register(cls, logger=None):
        DynamicModule._global_register(cls.PATH, cls, logger=logger)

    @staticmethod
    def settings_file_update(settings):
        """

        :param mra.settings.Settings settings:
        :return:
        """
        global Registry
        for name, cls in Registry.items():
            cls.load_settings(settings)

    @classmethod
    def load_settings(cls, settings):
        """

        :param mra.settings.Settings settings:
        :return:
        """
        cls.SETTINGS = settings.get(cls.PATH, Settings())
