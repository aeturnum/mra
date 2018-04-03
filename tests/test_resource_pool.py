import unittest
import asyncio

from mra.resource_pool import ResourcePool, ResourcePoolException

class ResourcePoolTest(unittest.TestCase):
    def async_test(self, func):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(func())

    def test_unlimited(self):
        async def test():
            # reset
            ResourcePool.MAX_ALLOCATION = -1
            ResourcePool.SEMA = None
            try:
                for n in range(0, 1000):
                    # don't block forever if we screwed up
                    rp = await ResourcePool().acquire(True)
            except ResourcePoolException:
                self.assertTrue(False, 'Resource Pool did not respect unlimited value')


        self.async_test(test)

    def test_limited(self):
        async def test():
            # reset
            ResourcePool.MAX_ALLOCATION = 2
            ResourcePool.SEMA = None
            try:
                rp1 = await ResourcePool().acquire()
                rp2 = await ResourcePool().acquire()
                rp3 = await ResourcePool().acquire(True)
                self.assertTrue(False, 'Successfully exceeded limit')
            except ResourcePoolException:
                pass

        self.async_test(test)

    def test_re_use(self):
        async def test():
            # reset
            ResourcePool.MAX_ALLOCATION = 1
            ResourcePool.SEMA = None
            test_value = "test"

            # implicit delete
            with await ResourcePool().acquire(True) as pool:
                pool._resource = test_value

            try:
                pool = await ResourcePool().acquire(True)
                self.assertEqual(
                    pool._resource, test_value, 
                    f'Pool resource has value {pool._resource}, not {test_value}'
                )
            except ResourcePoolException:
                self.assertTrue(False, 'with block failed to free resource')


        self.async_test(test)

if __name__ == '__main__':
    unittest.main()