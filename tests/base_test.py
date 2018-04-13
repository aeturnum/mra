import unittest
import asyncio

from mra.actions.action import Action

class TestAction(Action):
    def __init__(self, *args):
        super().__init__()
        self.args = list(args)

    def __len__(self):
        return len(self.args)

    def __getitem__(self, item):
        return self.args[item]

    def __str__(self):
        return f'TestAction{self.args}'


class BaseTest(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(False)

    def async_test(self, func):
        self.loop.run_until_complete(func())