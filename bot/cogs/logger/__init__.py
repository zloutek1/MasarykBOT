import logging

from discord.ext import commands, tasks


from .processors import BotBackup
from .message_iterator import MessageIterator
from bot.utils import requires_database, Context

log = logging.getLogger(__name__)


class Logger(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.backup_running: bool = False

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.backup_running = False
        self.backup_task.start()

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def backup(self, _ctx: Context) -> None:
        await self._backup()

    @tasks.loop(hours=24)
    async def backup_task(self) -> None:
        log.info("running routine processors")
        await self._backup()

    async def _backup(self) -> None:
        if self.backup_running:
            raise RuntimeError('backup process is already running')
        log.info("processors started")
        self.backup_running = True
        await BotBackup().traverse_down(self.bot)
        self.backup_running = False
        log.info("processors finished")


@requires_database
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Logger(bot))
