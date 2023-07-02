import logging
import traceback

from discord import app_commands
from discord.ext import commands

log = logging.getLogger(__name__)

NESTED_EXCEPTIONS = (
    commands.CommandInvokeError,
    commands.errors.HybridCommandError,
    app_commands.errors.CommandInvokeError
)


class ErrorReporterService:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    async def log_trace(message: str) -> None:
        log.error(message)

    async def log_exception(self, exception: Exception, ctx: commands.Context[commands.Bot] | None = None) -> None:
        trace = self.format_exception(ctx, exception)
        await self.log_trace(trace)

    @staticmethod
    def format_exception(ctx: commands.Context[commands.Bot], exception: Exception) -> str:
        exception: Exception = exception
        while isinstance(exception, NESTED_EXCEPTIONS):
            exception = exception.original

        trace = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        if ctx.command:
            user = ctx.author.name
            if ctx.message.content:
                command = ctx.message.content
                return f'In #{ctx.channel} @{user} said:\n   {command}\n\n{trace}'
            else:
                params = ' '.join(map(str, ctx.kwargs.values()))
                command = f"{ctx.prefix}{ctx.command} {params}"
                return f'In #{ctx.channel} @{user} executed:\n   {command}\n\n{trace}'
        return trace
