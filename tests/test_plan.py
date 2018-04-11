import unittest
from os.path import split, join

from mra.management import Plan
from mra.task import Task
from mra.actions.simple_actions import Get

class ResourcePoolTest(unittest.TestCase):
    def test_basic(self):
        p = Plan(Task(Get('http://httpbin.org/get')))
        result = p.run()

if __name__ == '__main__':
    unittest.main()