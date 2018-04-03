from asyncio import Semaphore, Lock

# used to create the semaphore if required by the allocation
Sema_Lock = Lock()

class ResourcePoolException(Exception):
    pass

class ResourcePool(object):
    MAX_ALLOCATION = -1
    RESOURCES = []
    SEMA = None

    def __init__(self):
        self._resource = None
        self._allocated = False

    def __del__(self):
        self.release()

    def __enter__(self, *args):
        return self

    def __exit__(self, *args):
        self.release()

    async def acquire(self, attempt=False):
        await self._create_semaphore()
        self._resource = await self._allocate_resource(attempt)
        return self

    def release(self):
        if self.SEMA and self._allocated:
            print("pool deleted")
            self.RESOURCES.append(self._resource)
            self.SEMA.release()

    @property
    def resource(self):
        if not self._allocated:
            raise ResourcePoolException("Resource was never acquired!")
        return self._resource

    @classmethod
    async def _create_semaphore(cls):
        global Sema_Lock
        with (await Sema_Lock):
            if cls.SEMA is None and cls.MAX_ALLOCATION >= 0:
                cls.SEMA = Semaphore(cls.MAX_ALLOCATION)

            cls._create_global_values()

    async def _allocate_resource(self, attempt):
        if (self.SEMA):
            if attempt and self.SEMA.locked():
                raise ResourcePoolException("Semaphore is taken")
            await self.SEMA.acquire()

        # true either way
        self._allocated = True
        if len(self.RESOURCES):
        # return first old resource if we've already created it
            return self.RESOURCES.pop(0)

        return self._create_resource()

    # create any global values that all resources share
    @classmethod
    def _create_global_values(cls):
        pass

    # will be called when the semaphore is acquired
    # must be overidden
    def _create_resource(self):
        return None
