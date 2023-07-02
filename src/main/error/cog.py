import sys
import traceback

from discord.ext import commands

from core.context.__init__ import Context
from error.service import ErrorReporterService

REPLY_ON_ERRORS = (
    commands.UserInputError,
    commands.MissingRole,
    commands.NoPrivateMessage,
    commands.MissingPermissions,
    commands.BotMissingPermissions,
    commands.CommandNotFound
)


class ErrorReporter(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.service = ErrorReporterService(bot)

    @commands.Cog.listener()
    async def on_error(self, _event: str) -> None:
        trace = "".join(traceback.format_exception(*sys.exc_info()))
        await self.service.log_trace(trace)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, exception: commands.CommandError) -> None:
        if hasattr(ctx.command, "on_error"):
            return

        if isinstance(exception, commands.CommandOnCooldown):
            await ctx.send_error("Error", str(exception))
            return

        if isinstance(exception, REPLY_ON_ERRORS):
            await ctx.send_error("Error", str(exception))
            return

        trace = self.service.format_exception(ctx, exception)
        await self.service.log_trace(trace)

        await ctx.send_error("Error", trace)
