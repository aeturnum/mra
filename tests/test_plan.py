import unittest

from mra.management import Plan
from mra.task import Task
from mra.actions.simple_actions import Get, JsonCheck

from base_test import BaseTest


class PlanTest(BaseTest):
    def test_basic(self):
        p = Plan(Task(
            Get('http://httpbin.org/get'),
            JsonCheck({'url': 'http://httpbin.org/get', 'args': {}})
        ))
        result = p.run(print=False)
        for r in result:
            self.assertTrue(r.completed)


    def test_parallel(self):
        p = Plan(
            Task(
                Get('http://httpbin.org/get'),
                JsonCheck({'url': 'http://httpbin.org/get', 'args': {}})
            ),
            Task(
                Get('http://httpbin.org/get'),
                JsonCheck({'url': 'http://httpbin.org/get', 'args': {}})
            ),
            Task(
                Get('http://httpbin.org/get'),
                JsonCheck({'url': 'http://httpbin.org/get', 'args': {}})
            )
        )
        result = p.run(print=False)
        for r in result:
            self.assertTrue(r.completed)

    def test_bad_test(self):
        class BadGet(Get):
            async def actions(self, task_handle, previous):
                return super().actions(previous)

        # broken test
        p = Plan(Task(
            BadGet('http://httpbin.org/get')
        ))
        result = p.run(print=False)
        for r in result:
            self.assertFalse(r.completed)

if __name__ == '__main__':
    unittest.main()