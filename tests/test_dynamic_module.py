import unittest
from os.path import split, join

from mra.dynamic_module import DynamicModuleManager
from mra.http_pool import HTTPPool

resources = join(split(__file__)[0], 'resources')
blocking = join(resources, 'dynamic_module_blocking')
syntax = join(resources, 'dynamic_module_syntax')

class ResourcePoolTest(unittest.TestCase):
    def test_gather(self):
        DynamicModuleManager._reset_registry()
        DynamicModuleManager.gather({})
        # check some standard modules
        from mra.dynamic_module import Registry
        self.assertTrue(HTTPPool.PATH in Registry, "Expected class not populated")

    def test_blocking(self):
        # todo: update with a settings object
        DynamicModuleManager._reset_registry()
        global blocking
        DynamicModuleManager.gather({"modules": [blocking]})

    def test_syntax(self):
        # todo: update with a settings object
        DynamicModuleManager._reset_registry()
        global syntax
        DynamicModuleManager.gather({"modules": [syntax]})

if __name__ == '__main__':
    unittest.main()