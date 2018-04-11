import unittest

from mra.management import Plan
from mra.task import Task
from mra.actions.simple_actions import Get, DictCheck

from base_test import BaseTest

class ResourcePoolTest(BaseTest):
    def test_basic(self):
        p = Plan(Task(
            Get('http://httpbin.org/get'),
            DictCheck({'url': 'http://httpbin.org/get', 'args': {}})
        ))
        result = p.run()
        print(result)

if __name__ == '__main__':
    unittest.main()