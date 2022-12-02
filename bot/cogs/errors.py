import io
import logging
import sys
import traceback
from typing import Optional

import discord
from discord import File, app_commands
from discord.ext import commands
from discord.utils import get

from bot.utils import Context
from bot.constants import CONFIG

log = logging.getLogger(__name__)

REPLY_ON_ERRORS = (
    commands.UserInputError,
    commands.MissingRole,
    commands.NoPrivateMessage,
    commands.MissingPermissions,
    commands.BotMissingPermissions,
    commands.CommandNotFound
)



class ErrorCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @commands.Cog.listener()
    async def on_error(self, _event: str) -> None:
        trace = "".join(traceback.format_exception(*sys.exc_info()))
        await self.log_error(trace)


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

        while isinstance(error, (commands.CommandInvokeError, commands.errors.HybridCommandError, app_commands.errors.CommandInvokeError)):
            error = error.original

        trace = self._format_error(ctx, error)
        await self.log_error(trace, guild=ctx.guild)


    async def log_error(self, message: str, guild: Optional[discord.Guild] = None) -> None:
        log.error(message)

        if guild is not None:
            if error_chanel := self.get_guild_error_channel(guild):
                await self.log_error_to_channel(error_chanel, message)
        else:
            await self.log_error_to_all_guilds(message)


    @staticmethod
    async def log_error_to_channel(error_channel: discord.abc.Messageable, message: str) -> None:
        if len(message) < 1990:
            await error_channel.send(f"```\n{message}\n```")
        else:
            fp = io.BytesIO(message.encode('utf-8'))
            await error_channel.send(file=File(fp=fp, filename=f"error.txt"))


    async def log_error_to_all_guilds(self, message: str) -> None:
        for guild_config in CONFIG.guilds:
            if not (channel_id := guild_config.logs.errors):
                continue
            error_channel = self.bot.get_channel(channel_id)
            await self.log_error_to_channel(error_channel, message)


    def get_guild_error_channel(self, guild: discord.Guild) -> Optional[discord.abc.Messageable]:
        if not (guild_config := get(CONFIG.guilds, id=guild.id)):
            return None
        if not (channel_id := guild_config.logs.errors):
            return None
        return self.bot.get_channel(channel_id)


    @staticmethod
    def _format_error(ctx: commands.Context, error: Exception) -> str:
        trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
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



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ErrorCog(bot))
