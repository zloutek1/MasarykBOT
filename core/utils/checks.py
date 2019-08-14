import aiomysql
from discord.ext import commands
from functools import wraps

from core.utils.db import Database


def needs_database(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not hasattr(self.bot, "db"):
            return False

        if hasattr(self, "db") and not self.db.cursor.closed:
            return await func(self, *args, **kwargs)

        pool = self.bot.db.pool
        if not pool:
            return

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                self.db = Database(conn, cursor, pool)

                retval = await func(self, *args, **kwargs)
        return retval
    return wrapper
