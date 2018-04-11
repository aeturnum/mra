import unittest
import asyncio


class BaseTest(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(True)

    def async_test(self, func):
        self.loop.run_until_complete(func())