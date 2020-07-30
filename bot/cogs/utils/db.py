import asyncio
import asyncpg

from . import schemas


class DBAcquire:
    def __init__(self, db, timeout):
        self.db = db
        self.timeout = timeout

    def __await__(self):
        return self.db._acquire(self.timeout).__await__()

    async def __aenter__(self):
        await self.db._acquire(self.timeout)
        return self.db._conn

    async def __aexit__(self, *args):
        await self.db.release()


class Database:
    def __init__(self, pool):
        self.pool = pool
        self._conn = None

    @property
    def conn(self):
        return self._conn if self._conn else self.pool

    @classmethod
    def connect(cls, url):
        loop = asyncio.get_event_loop()
        pool = loop.run_until_complete(asyncpg.create_pool(url, command_timeout=60))
        return Database(pool)

    async def _acquire(self, timeout):
        if self._conn is None:
            self._conn = await self.pool.acquire(timeout=timeout)
        return self._conn

    def acquire(self, *, timeout=None):
        """Acquires a database connection from the pool. e.g. ::
            async with self.acquire():
                await self.conn.execute(...)
        or: ::
            await self.acquire()
            try:
                await self.conn.execute(...)
            finally:
                await self.release()
        """
        return DBAcquire(self, timeout)

    async def release(self):
        """Releases the database connection from the pool.
        Useful if needed for "long" interactive commands where
        we want to release the connection and re-acquire later.
        Otherwise, this is called automatically by the bot.
        """
        if self._conn is not None:
            await self.pool.release(self._conn)
            self._conn = None

    async def insert_guilds(self, data):
        async with self.acquire():
            await self.conn.executemany(schemas.SQL_INSERT_GUILD, data)

    async def insert_categories(self, data):
        async with self.acquire():
            await self.conn.executemany(schemas.SQL_INSERT_CATEGORY, data)

    async def insert_roles(self, data):
        async with self.acquire():
            await self.conn.executemany(schemas.SQL_INSERT_ROLE, data)

    async def insert_members(self, data):
        async with self.acquire():
            await self.conn.executemany(schemas.SQL_INSERT_MEMBER, data)

    async def insert_channels(self, data):
        async with self.acquire():
            await self.conn.executemany(schemas.SQL_INSERT_CHANNEL, data)
