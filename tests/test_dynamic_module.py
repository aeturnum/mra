import unittest
from os.path import split, join

from mra.dynamic_module import DynamicModule
from mra.http_pool import HTTPPool

resources = join(split(__file__)[0], 'resources')
blocking = join(resources, 'dynamic_module_blocking')
syntax = join(resources, 'dynamic_module_syntax')

class ResourcePoolTest(unittest.TestCase):
    def test_gather(self):
        DynamicModule._reset_registry()
        DynamicModule.gather({})
        # check some standard modules
        from mra.dynamic_module import Registry
        self.assertTrue(HTTPPool.PATH in Registry, "Expected class not populated")

    def test_blocking(self):
        # todo: update with a settings object
        DynamicModule._reset_registry()
        global blocking
        DynamicModule.gather({"modules": [blocking]})

    def test_syntax(self):
        # todo: update with a settings object
        DynamicModule._reset_registry()
        global blocking
        DynamicModule.gather({"modules": [syntax]})

if __name__ == '__main__':
    unittest.main()