import logging
from discord.ext import commands

from bot.cogs.utils.context import Context
from .BotBackup import BotBackup

log = logging.getLogger(__name__)


class Logger(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="backup")
    @commands.has_permissions(administrator=True)
    async def _backup(self) -> None:
        await self.backup()

    async def backup(self) -> None:
        log.info("backup started")
        await BotBackup().traverse_down(self.bot)
        log.info("backup finished")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Logger(bot))
