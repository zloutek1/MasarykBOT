import logging
import traceback

from bot.cogs.utils.context import Context
from bot.constants import Config
from disnake.abc import Messageable
from disnake.ext import commands
from disnake.utils import get

log = logging.getLogger(__name__)


class Errors(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: commands.CommandError) -> None:
        if hasattr(ctx.command, "on_error"):
            return

        if isinstance(error, (commands.BadArgument, commands.MissingRequiredArgument, commands.MissingRole, commands.errors.BadUnionArgument)):
            await ctx.send_error(str(error))
            return

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send_error(str(error))
            return

        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send_error('This command cannot be used in private messages.')
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send_error("Sorry. You don't have permissions to use this command")
            return

        for just_printable in [commands.ArgumentParsingError, commands.BotMissingPermissions]:
            if isinstance(error, just_printable):
                await ctx.send_error(str(error))
                return

        if isinstance(error, commands.CommandInvokeError):
            await self.log_error(ctx, error.original)
            return

        await self.log_error(ctx, error)

    async def log_error(self, ctx: Context, error: Exception) -> None:
        if ctx.command is None:
            return

        command_name = ctx.command.qualified_name
        trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        msg = f'In {command_name}:\n{trace}'

        log.error(msg)

        if ctx.guild is None:
            return

        if (guild_config := get(Config.guilds, id=ctx.guild.id)) is None:
            return

        channel_id = guild_config.logs.errors
        if channel_id and (channel := self.bot.get_channel(channel_id)) is not None:
            if not isinstance(channel, Messageable):
                return

            part = ""
            for line in msg.split("\n"):
                if len(part) + len(line) < 1900:
                    part += line + "\n"
                elif len(line) >= 1900:
                    await channel.send(f"`Line too long to display`")
                    part = ""
                else:
                    await channel.send(f"```\n{part}\n```")
                    part = line
            if part:
                await channel.send(f"```\n{part}\n```")

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Errors(bot))
