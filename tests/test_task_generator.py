import unittest

from base_test import BaseTest, TestAction
from mra.actions.task_generator import ArgFromList, ActionStandin, TaskGenerator, MultipleActions, MultipleTasks


class TaskGeneratorTest(BaseTest):
    def test_standin(self):
        a = ActionStandin(TestAction, "plain", ArgFromList(['a', 'b']), 'c')

        result = [r for r in a]
        self.assertEqual(2, len(result))
        self.assertEqual('a', result[0][1])
        self.assertEqual('b', result[1][1])

    def test_task_gen(self):
        # should generate two task lists
        tg = TaskGenerator(TestAction(1), MultipleTasks(TestAction, 'a', ArgFromList(['b', 'c']), 'c'))

        tasks = [r for r in tg]
        # two tasks
        self.assertEqual(2, len(tasks))
        # each task has two actions
        self.assertEqual(2, len(tasks[0]))
        self.assertEqual(2, len(tasks[1]))

        self.assertEqual(tasks[0].actions[0][0], 1)
        self.assertEqual(tasks[0].actions[1][0], 'a')
        self.assertEqual(tasks[0].actions[1][1], 'b')
        self.assertEqual(tasks[0].actions[1][2], 'c')

        self.assertEqual(tasks[1].actions[0][0], 1)
        self.assertEqual(tasks[1].actions[1][0], 'a')
        self.assertEqual(tasks[1].actions[1][1], 'c')
        self.assertEqual(tasks[1].actions[1][2], 'c')

    def test_action_gen(self):
        # should generate two task lists
        tg = TaskGenerator(TestAction(1), MultipleActions(TestAction, 'a', ArgFromList(['b', 'c']), 'c'))

        tasks = [r for r in tg]
        # one task
        self.assertEqual(1, len(tasks))
        # task has three actions
        self.assertEqual(3, len(tasks[0]))

        self.assertEqual(tasks[0].actions[0][0], 1)
        self.assertEqual(tasks[0].actions[1][0], 'a')
        self.assertEqual(tasks[0].actions[1][1], 'b')
        self.assertEqual(tasks[0].actions[1][2], 'c')
        self.assertEqual(tasks[0].actions[2][0], 'a')
        self.assertEqual(tasks[0].actions[2][1], 'c')
        self.assertEqual(tasks[0].actions[2][2], 'c')

if __name__ == '__main__':
    unittest.main()