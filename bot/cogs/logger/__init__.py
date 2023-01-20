import logging
from contextlib import suppress

import inject
from discord.ext import commands, tasks

from bot.cogs.logger.processors import Backup, setup_injections
from bot.cogs.logger.message_iterator import MessageIterator
from bot.cogs.logger.history_iterator import HistoryIterator
from bot.utils import requires_database, Context

__all__ = [
    'MessageIterator',
    'HistoryIterator',
    'LoggerCog', 'setup',
    'BackupAlreadyRunning',
    'setup_injections'
]

log = logging.getLogger(__name__)


class BackupAlreadyRunning(RuntimeError):
    pass


class LoggerCog(commands.Cog):
    @inject.autoparams('backup_bot')
    def __init__(self, bot: commands.Bot, bot_backup: Backup[commands.Bot]) -> None:
        self.bot = bot
        self.backup_running: bool = False
        self.bot_backup = bot_backup

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
        with suppress(BackupAlreadyRunning):
            await self._backup()

    async def _backup(self) -> None:
        if self.backup_running:
            raise BackupAlreadyRunning('backup process is already running')
        log.info("processors started")
        self.backup_running = True
        await self.bot_backup.traverse_down(self.bot)
        self.backup_running = False
        log.info("processors finished")


@requires_database
async def setup(bot: commands.Bot) -> None:
    injector = inject.get_injector_or_die()
    bot_backup = injector.get_instance(Backup[commands.Bot])

    await bot.add_cog(LoggerCog(bot, bot_backup))
