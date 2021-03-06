import logging
import traceback

from discord.ext import commands
from discord.utils import get

from bot.constants import Config


log = logging.getLogger(__name__)


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        for ignore_error in [commands.BadArgument, commands.MissingRequiredArgument, commands.MissingRole, commands.errors.BadUnionArgument]:
            if isinstance(error, ignore_error):
                return

        if hasattr(ctx.command, "on_error"):
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
                await ctx.send_error(error)
                return

        if isinstance(error, commands.CommandInvokeError):
            await self.log_error(ctx, error.original)
            return

        await self.log_error(ctx, error)

    async def log_error(self, ctx, error):
        command_name = ctx.command.qualified_name
        trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        msg = f'In {command_name}:\n{trace}'

        log.error(msg)

        guild_config = get(Config.guilds, id=ctx.guild.id)
        channel_id = guild_config.logs.errors
        if channel_id and (channel := self.bot.get_channel(channel_id)) is not None:
            part = ""
            for line in msg.split("\n"):
                if len(part) + len(line) < 1900:
                    part += line + "\n"
                elif len(line) >= 1900:
                    await channel.send(f"```\n{part}\n```")
                    for i in range(0, len(line), 1900):
                        await channel.send(f"```\n{chunk}\n```")
                    part = ""
                else:
                    await channel.send(f"```\n{part}\n```")
                    part = line
            if part:
                await channel.send(f"```\n{part}\n```")

def setup(bot):
    bot.add_cog(Errors(bot))