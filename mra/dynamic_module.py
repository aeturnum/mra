import importlib.util
import inspect
from os.path import split, basename, join
import os
import multiprocessing
import time

# global registry
Registry = {}
# Registry_Lock = Lock()

# default location for actions
_DEFAULT_ACTIONS = (
    # package directory
    split(__file__)[0],
)


_DRY_RUN_TIMEOUT = 5

class DynamicModule(object):
    PATH = "Global"

    def __init__(self):
        self.settings = {}

    @staticmethod
    def _global_register(path, module):
        global Registry
        global Registry_Lock
        # with (await Registry_Lock):
        if path in Registry:
            raise Exception(
                f"Can't register {module}. Path {path} is already registered to module {Registry[path]}!"
            )
        Registry[path] = module
        print(f'Added {module} under path "{path}"')

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
        self.settings = settings_dict.get(self.PATH, None)

    @staticmethod
    def _gather_file(path, test_process=False):
        # this must be called in a thread because if the module exec blocks, it must be killed
        module_name = basename(path).split(".")[0]

        # todo: parse module name
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except SyntaxError:
            print(f'File {path} contains a syntax error - skipping')
            # exit with a bad code if we're being called in a process
            if test_process:
                exit(1)
        except:
            # exit with a bad code if we're being called in a process
            if test_process:
                exit(1)
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and obj.__module__ == module_name and issubclass(obj, DynamicModule):
                # this will be called in a process first to ensure the process works
                if not test_process:
                    DynamicModule._global_register(obj.PATH, obj)



    @staticmethod
    def gather(settings):
        # todo: add directory enumeration
        global _DEFAULT_ACTIONS
        for action_directory in _DEFAULT_ACTIONS:
            for dir_name, sub_dirs, file_list in os.walk(action_directory):
                for file_name in file_list:
                    if file_name.endswith(".py"):
                        path = join(dir_name, file_name)
                        process = multiprocessing.Process(
                            target=DynamicModule._gather_file,
                            args=(path, True) # dry run
                        )
                        process.start()
                        # we run this in a seperate process first, because they can be killed, unlike
                        # python threads. This allows us to detect blocking python files.
                        process.join(timeout=_DRY_RUN_TIMEOUT)
                        if process.is_alive():
                            process.terminate()
                            process.join()
                            print(f'File {path} did not terminate when loading module, probably blocks. Skipping.')
                        else:
                            if process.exitcode == 0:
                                # actually add the modules
                                DynamicModule._gather_file(path)
                            else:
                                print(f'File {path} has a non-zero exit code, indicating problems. Skipping.')
                #DynamicModule._gather_file(_DEFAULT_ACTIONS[0])



