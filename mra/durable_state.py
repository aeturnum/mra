import aiosqlite

from mra.dynamic_module import DynamicModule

import json

SQLITE_DATABASE_NAME = 'SQLITE_DATABASE_NAME'
_DEFAULT_DB_NAME = 'task_state.db'


class DurableState(DynamicModule):
    PATH = "Resource.SqlitePool.DurableState"

    _state_table_create = f'CREATE TABLE IF NOT EXISTS states (id INTEGER PRIMARY KEY ASC, type INTEGER, state VARCHAR);'
    _load_state_query = 'SELECT * from states where id = {db_id}'
    _create_state_query = 'INSERT INTO states (type, state) VALUES (?, ?)'
    _update_state_query = 'UPDATE states SET state = (?) WHERE id = {db_id}'
    _delete_state_query = 'DELETE from states where id = {db_id}'

    def __init__(self, type_id:int, db_id:int=None):
        super().__init__()
        self._state = {'type': type_id}
        self.durable_id = db_id
        self._state_synced = False

    async def _init(self):
        async with aiosqlite.connect(cls._db_name()) as db:
            # should be safe to run many time
            await db.execute(cls._state_table_create)

        return None


    async def _load_state(self):
        if self.durable_id is not None:
            await self._init()
            async with aiosqlite.connect(self.db_name) as db:
                cursor = await db.execute(self._load_state_query.format(db_id=self.durable_id))
                if cursor.rowcount != -1:
                    print(cursor.rowcount)
                    raise Exception("Somehow there's a duplicate row, burn it all down.")
                row = await cursor.fetchone()
                # (id, type, state)
                self._state = json.loads(row[2].replace('\\"','"'))

                self._state_synced = True

            # todo: use this somehow

    async def _create_state(self):
        if self.durable_id is None:

            await self._init()
            async with aiosqlite.connect(self.db_name) as db:
                cursor = await db.execute(
                    self._create_state_query.format(db_id = self.durable_id),
                    [self._state['type'], self.str_state]
                )
                self.durable_id = cursor.lastrowid
                await db.commit()

                self._state_synced = True

    async def _barrier(self):
        if not self._state_synced:
            if self.durable_id:
                await self._load_state()
            else:
                await self._create_state()

    def __getitem__(self, key:str) -> any:
        return self._state.get(key, None)

    @property
    def str_state(self):
        return json.dumps(self._state).replace('"', '\\"')

    @classmethod
    def _db_name(cls):
        global SQLITE_DATABASE_NAME
        global _DEFAULT_DB_NAME

        name = _DEFAULT_DB_NAME
        if cls.SETTINGS:
            name = cls.SETTINGS[SQLITE_DATABASE_NAME]

        return name

    @property
    def db_name(self):
        return self._db_name()

    async def update(self, updates:dict):
        await self._barrier()

        for key, value in updates.items():
            if value is None:
                del self._state[key]
            else:
                self._state[key] = value
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(self._update_state_query.format(db_id = self.durable_id), [self.str_state])
            await db.commit()

    async def delete(self):
        await self._barrier()

        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(self._delete_state_query.format(db_id=self.durable_id))


    async def read(self):
        await self._barrier()
        # copy
        return dict(self._state)


