from discord.ext import commands
from functools import wraps


def needs_database(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not hasattr(self.bot, "db"):
            return False

        self.db = self.bot.db.connect()
        if not self.db:
            return False

        return await func(self, *args, **kwargs)
    return wrapper
