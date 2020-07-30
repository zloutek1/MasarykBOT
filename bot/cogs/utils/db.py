import asyncio
import asyncpg


class Database:
    def __init__(self, pool):
        self.pool = pool

    @classmethod
    def connect(cls, url):
        loop = asyncio.get_event_loop()
        pool = loop.run_until_complete(asyncpg.create_pool(url, command_timeout=60))
        return Database(pool)


