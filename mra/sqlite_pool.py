import aiosqlite

from mra.resource_pool import ResourcePool

SQLITE_DATABASE_NAME = 'SQLITE_DATABASE_NAME'
_DEFAULT_DB_NAME = 'task_state.db'


class SQLITEPool(ResourcePool):
    PATH = 'Resource.Sqlite'
    MAX_ALLOCATION = 10

    # should be handled at another level
    _state_table = "states"
    _state_table_create = f'CREATE TABLE {_state_table}(id INTEGER PRIMARY KEY ASC, object_id INTEGER, state TEXT);'

    # def __init__(self):
    #     super().__init__()

    @classmethod
    async def _create_resource(cls):
        global SQLITE_DATABASE_NAME
        global _DEFAULT_DB_NAME
        # todo: must 'dirty' old connections if a new file is specified
        name = _DEFAULT_DB_NAME
        if cls.SETTINGS:
            name = cls.SETTINGS[SQLITE_DATABASE_NAME]

        connection = aiosqlite.connect(name)
        # should be safe to run many time
        await connection.execute(cls._state_table_create)
        return connection
