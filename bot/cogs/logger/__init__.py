import logging

from discord.ext import commands, tasks

from bot.cogs.utils.context import Context

from .processors import BotBackup
from .message_iterator import MessageIterator


log = logging.getLogger(__name__)


class Logger(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.backup_task.start()

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def backup(self, ctx: Context) -> None:
        await self._backup()

    @tasks.loop(hours=24)
    async def backup_task(self) -> None:
        log.info("running routine processors")
        await self._backup()

    async def _backup(self) -> None:
        log.info("processors started")
        await BotBackup().traverse_down(self.bot)
        log.info("processors finished")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Logger(bot))
