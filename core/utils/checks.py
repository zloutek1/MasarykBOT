from discord.ext import commands


def needs_database(func):
    async def wrapper(self, *args, **kwargs):
        if not hasattr(self.bot, "db"):
            return False

        self.db = self.bot.db.connect()
        if not self.db:
            return False

        return await func(self, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper
