import unittest
import asyncio
from os.path import exists
from os import unlink

from mra.durable_state import DurableState

class ResourcePoolTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if exists('./task_state.db'):
            unlink('./task_state.db')

    def async_test(self, func):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(func())

    def test_basic(self):
        async def test():
            # reset
            ds = DurableState(0)
            state = await ds.read()
            self.assertIn("type", state)
            self.assertEqual(state['type'], 0)

        self.async_test(test)

    def test_update(self):
        async def test():
            # reset
            test_id = None
            ds = DurableState(0)
            await ds.update({"foo":"bar"})
            test_id = ds.durable_id
            del ds
            ds = DurableState(0, test_id)
            state = await ds.read()
            self.assertIn("foo", state)
            self.assertEqual(state['foo'], 'bar')

        self.async_test(test)

    def test_delete(self):
        async def test():
            # reset
            test_id = None
            ds = DurableState(0)
            await ds.update({"foo":"bar"})
            test_id = ds.durable_id
            await ds.delete()
            del ds
            ds = DurableState(0, test_id)
            state = await ds.read()
            self.assertNotIn("foo", state)

        self.async_test(test)

if __name__ == '__main__':
    unittest.main()