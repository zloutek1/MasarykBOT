from discord.ext import commands


class BotError(Exception):
    """Base exception for all NabBot related errors."""
    pass


class UnathorizedUser(commands.CheckFailure, BotError):
    pass
