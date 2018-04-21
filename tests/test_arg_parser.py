import unittest

from mra.dynamic_module import DynamicModuleManager
from mra.management import ArgParser
from mra.actions.simple_actions import Get
from mra.util import is_instance

from base_test import BaseTest


class ArgParseTest(BaseTest):
    def compare(self, a, b):
        for idx, arg in enumerate(a):
            self.assertEqual(arg, b[idx])

    def test_easy(self):
        self.compare(
            ArgParser('("a")'),
            ['a']
        )

    def test_easy_2(self):
        self.compare(
            ArgParser('(123, \'d\')'),
            [123, "d"]
        )

        self.compare(
            ArgParser('(123.23, \'d\')'),
            [123.23, "d"]
        )

    def test_function(self):
        self.compare(
            ArgParser('(123, foo(), \'d\')'),
            [123, 'foo()', "d"]
        )

    def test_function_args(self):
        self.compare(
            ArgParser('(123, foo(123, "d"), \'d\')'),
            [123, 'foo(123, "d")', "d"]
        )

    def test_function_function_args(self):
        self.compare(
            ArgParser('(123, foo(bar(\'hello\'), "d"), \'d\')'),
            [123, 'foo(bar(\'hello\'), "d")', "d"]
        )

    def test_class(self):
        DynamicModuleManager._reset_registry()
        DynamicModuleManager.gather({})
        ap = ArgParser('Get("test.com")')
        action = [a for a in ap][0]
        self.assertTrue(is_instance(action, Get))
        self.assertEqual(action.url, 'test.com')

    def test_class_2(self):
        DynamicModuleManager._reset_registry()
        DynamicModuleManager.gather({})
        ap = ArgParser('Get(Get("test.com"))')
        action = [a for a in ap][0]
        self.assertTrue(is_instance(action, Get))
        self.assertTrue(is_instance(action.url, Get))
        self.assertEqual(action.url.url, 'test.com')


if __name__ == '__main__':
    unittest.main()