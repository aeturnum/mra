import unittest
from os.path import split, join

from mra.management import JobSpec
from mra.dynamic_module import DynamicModuleManager

from base_test import BaseTest
from mra.actions.simple_actions import Get
# a = ActionStandin(TestAction, "plain", ArgFromList(['a', 'b']), 'c')

resources = join(split(__file__)[0], 'resources')
spec_dir = join(resources, 'job_spec')


class JobSpecTest(BaseTest):
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
        actions = [action for action in plan.tasks[0]]
        self.assertEqual(len(actions), 3)

        expected_urls = ['www.test.com', 'a', 'b']
        for idx, action in enumerate(actions):
            self.assertEqual(action.PATH, Get.PATH)
            self.assertEqual(action.url, expected_urls[idx])

    def test_file(self):
        global spec_dir
        js = [js for js in JobSpec.load_directory({}, spec_dir)]
        self.assertEqual(len(js), 1)
        js = js[0]
        plan = js.create_plan()
        actions = [action for action in plan.tasks[0]]
        self.assertEqual(len(actions), 3)

        expected_urls = ['www.test.com', 'a', 'b']
        for idx, action in enumerate(actions):
            self.assertEqual(action.PATH, Get.PATH)
            self.assertEqual(action.url, expected_urls[idx])

if __name__ == '__main__':
    unittest.main()