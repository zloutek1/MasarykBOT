import io
import logging
import traceback

from discord import File
from discord.abc import Messageable
from discord.ext import commands
from discord.utils import get

from bot.cogs.utils.context import Context
from bot.constants import CONFIG

log = logging.getLogger(__name__)

REPLY_ON_ERRORS = (
    commands.BadArgument,
    commands.MissingRequiredArgument,
    commands.MissingRole,
    commands.errors.BadUnionArgument,
    commands.NoPrivateMessage,
    commands.MissingPermissions,
    commands.ArgumentParsingError,
    commands.BotMissingPermissions
)


class Errors(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: commands.CommandError) -> None:
        if hasattr(ctx.command, "on_error"):
            return

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send_error(str(error), delete_after=error.retry_after)
            return

        if isinstance(error, REPLY_ON_ERRORS):
            await ctx.send_error(str(error))
            return

        if isinstance(error, commands.CommandInvokeError):
            await self.log_error(ctx, error.original)
            return

        await self.log_error(ctx, error)

    async def log_error(self, ctx: Context, error: Exception) -> None:
        trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))

        if ctx.command:
            user = ctx.author.name
            msg = ctx.message.content
            msg = f'In #{ctx.channel} @{user} said:\n   {msg}\n\n{trace}'
        else:
            msg = trace

        log.error(msg)

        if ctx.guild is None:
            return

        if not (guild_config := get(CONFIG.guilds, id=ctx.guild.id)):
            return

        if not (channel_id := guild_config.logs.errors):
            return

        if not (channel := await self.bot.fetch_channel(channel_id)):
            return

        if not isinstance(channel, Messageable):
            return

        if len(msg) < 1990:
            await channel.send(f"```\n{msg}\n```")
        else:
            fp = io.BytesIO(msg.encode('utf-8'))
            await channel.send(file=File(fp=fp, filename=f"{type(error).__name__}.txt"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Errors(bot))
