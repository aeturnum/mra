from mra.sqlite_pool import SQLITEPool

class DurableState(SQLITEPool):
    PATH = "Resource.SqlitePool.DurableState"

    def __init__(self, dbid=None):
        super().__init__()
        self._resources = {}
        self._dbid = dbid

    async def _load_state(self):
        pass

    async def update(self, updates):
        pass

