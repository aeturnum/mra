import unittest

from mra.management import JobSpec
from mra.dynamic_module import DynamicModuleManager

from base_test import BaseTest
# a = ActionStandin(TestAction, "plain", ArgFromList(['a', 'b']), 'c')

class PlanTest(BaseTest):
    def test_dictionary(self):
        DynamicModuleManager._reset_registry()
        DynamicModuleManager.gather({})
        spec = {
            'title': 'etc',
            'actions': [
                "Get('www.test.com')",
                "MultipleActions('Get', \"ArgFromList(['a', 'b'])\")"
            ]
        }
        js = JobSpec({}, spec, 'none')
        plan = js.create_plan()
        print([action for action in plan.tasks[0]])

if __name__ == '__main__':
    unittest.main()