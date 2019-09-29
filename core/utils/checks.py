import aiomysql
import discord
from functools import wraps

from core.utils.db import Database


def needs_database(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not hasattr(self.bot, "db"):
            return False

        pool = self.bot.db.pool
        if not pool:
            return

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                kwargs["db"] = Database(conn, cursor, pool)
                retval = await func(self, *args, **kwargs)

        return retval

        if not hasattr(self, "db"):
            self.db = Database(conn, cursor, pool)

    return wrapper


def safe(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except discord.errors.NotFound:
            pass
    return wrapper
