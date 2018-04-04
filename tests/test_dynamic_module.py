import unittest

from mra.dynamic_module import DynamicModule

class ResourcePoolTest(unittest.TestCase):
    def test_gather(self):
        DynamicModule.gather({})

if __name__ == '__main__':
    unittest.main()