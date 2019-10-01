import aiomysql
import discord
from functools import wraps

from core.utils.db import Database


def needs_database(func):
    """
    this function is a wrapper to a command or an event function
    this tells the bot that the function will access the
    database in its body.
    @needs_database established a database connection and passes
    the Databse object into a db variable in your function.

    example:
    ```
        @commands.command()
        @needs_database
        async def my_command(self, ctx, *args, *, db: Database=None)

        @commands.Cog.listener()
        @needs_database
        async def my_event(self, *args, *, db: Database=None)
    ```
    """
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
    """
    a shortcut for try: except Notfound:
    used mostly to delete a message without an error
    used as `safe(ctx.message.delete)()`
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except discord.errors.NotFound:
            pass
    return wrapper
