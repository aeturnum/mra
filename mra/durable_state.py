import aiosqlite
import jsonpickle
import copy

from mra.dynamic_module import DynamicModule
from mra.logger import Logger

import json

SQLITE_DATABASE_NAME = 'SQLITE_DATABASE_NAME'
_DEFAULT_DB_NAME = 'task_state.db'


class DBError(Exception):
    pass


class DBDict(dict, Logger):
    _create_state_query = 'INSERT INTO states (type, state) VALUES (?, ?)'
    _update_state_query = 'UPDATE states SET state = (?) WHERE id = {db_id}'
    _load_state_query = 'SELECT * from states where id = {db_id}'
    _delete_state_query = 'DELETE from states where id = {db_id}'

    def __init__(self, data, db_id=None):
        dict.__init__(self, data)
        Logger.__init__(self)
        self.db_id = db_id
        self._loaded = False

    async def _execute(self, db: aiosqlite.Connection, statement: str, args: list=None):
        if args is None:
            args = []

        self.log_spew('statement: {}, args: {}', statement, args)
        return await db.execute(statement, args)

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def str_state(self) -> str:
        return jsonpickle.dumps(self.dict())

    @property
    def next(self) -> int:
        return self['next']

    @next.setter
    def next(self, value: int):
        self['next'] = value

    @property
    def prev(self) -> int:
        return self['prev']

    @prev.setter
    def prev(self, value: int):
        self['prev'] = value

    # returns dbid
    async def _create(self, db: aiosqlite.Connection) -> int:
        self._loaded = True
        return 0
        # cursor = await self._execute(db, self._create_state_query, [self['type'], self.str_state])
        # await db.commit()
        # self.db_id = cursor.lastrowid
        # self._loaded = True
        # return self.db_id

    async def _load(self, db: aiosqlite.Connection) -> None:
        self._loaded = True
        pass
        # cursor = await self._execute(db, self._load_state_query.format(db_id=self.db_id))
        # if cursor.rowcount != -1:
        #     print(cursor.rowcount)
        #     raise DBError("Somehow there's a duplicate row, burn it all down.")
        # row = await cursor.fetchone()
        # if row is None:
        #     raise DBError("ID does not exist")
        # # (id, type, state)
        # saved_item = jsonpickle.loads(row[2])
        # for key, item in saved_item.items():
        #     self[key] = item
        # self._loaded = True

    async def _update(self, db: aiosqlite.Connection) -> None:
        pass
        # await self._execute(db, self._update_state_query.format(db_id=self.db_id), [self.str_state])
        # await db.commit()

    async def _delete(self, db: aiosqlite.Connection) -> None:
        pass
        # await self._execute(db, self._delete_state_query.format(db_id=self.db_id))
        # await db.commit()

    def copy(self) -> 'DBDict':
        new_dbd = DBDict(self, self.db_id)
        new_dbd._lh = copy.copy(self._lh)
        return new_dbd

    def dict(self) -> dict:
        return dict(self)

    def __str__(self):
        return 'S|{id}<{items}>'.format(items=self._dict_to_str(self), id=self.db_id)


class DurableState(DynamicModule):
    PATH = "Resource.SqlitePool.DurableState"

    _state_table_create = 'CREATE TABLE IF NOT EXISTS states (id INTEGER PRIMARY KEY ASC, type INTEGER, state VARCHAR);'

    def __init__(self, type_id: int=0, db_id: int=None):
        super().__init__()
        self._state = DBDict({'type': type_id, 'previous': None, 'next': None}, db_id)
        self._adopt(self._state)
        self._state_synced = False

    @property
    def durable_id(self):
        return self._state.db_id

    async def _init_db(self):
        async with aiosqlite.connect(self._db_name()) as db:
            # should be safe to run many time
            await db.execute(self._state_table_create)

        return None

    async def _load_state(self):
        if self.durable_id is not None:
            await self._init_db()
            async with aiosqlite.connect(self.db_name) as db:
                await self._state._load(db)
                self._state_synced = True

    async def _create_state(self):
        if self.durable_id is None:
            await self._init_db()
            async with aiosqlite.connect(self.db_name) as db:
                await self._state._create(db)
                self._state_synced = True

    async def _barrier(self):
        if not self._state_synced:
            if self.durable_id:
                try:
                    await self._load_state()
                except DBError:
                    await self._create_state()
            else:
                await self._create_state()

    def __getitem__(self, key:str) -> any:
        return self._state.get(key, None)

    def get(self, key, default=None):
        return self._state.get(key, default)

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

    async def setup(self):
        await self._barrier()

    async def update(self, updates:dict):
        await self._barrier()

        # copy of dirty state
        dirty_state = self._state.copy()
        for key, value in updates.items():
            if value is None:
                del self._state[key]
            else:
                self._state[key] = value
        async with aiosqlite.connect(self.db_name) as db:
            # set old id
            self._state.prev = self.durable_id
            # create new entry
            await self._state._create(db)
            # could also be done though self.durable_id, but that's confusing to read
            dirty_state.next = self._state.db_id
            await dirty_state._update(db)

    async def delete(self):
        await self._barrier()

        state = self._state
        async with aiosqlite.connect(self.db_name) as db:
            while state.prev != None:
                await state._delete(db)
                # switch to prev
                state.db_id = state.prev
                # load
                try:
                    await state._load(db)
                except DBError:
                    break

    async def read(self):
        await self._barrier()
        # copy
        return dict(self._state)

    def __str__(self):
        return f'DS|{self._state}'
