import logging

import discord
import inject
from discord import Thread

from bot.cogs.logger.message_iterator import MessageIterator
from bot.db import ThreadMapper, ThreadRepository, ThreadEntity
from bot.cogs.logger.processors._base import Backup

log = logging.getLogger(__name__)


class ThreadBackup(Backup[Thread]):
    @inject.autoparams()
    def __init__(self, repository: ThreadRepository, mapper: ThreadMapper) -> None:
        super().__init__()
        self.repository = repository
        self.mapper = mapper

    @inject.autoparams()
    async def traverse_up(self, thread: Thread, channel_backup: Backup[discord.abc.GuildChannel]) -> None:
        if not thread.parent:
            return
        await channel_backup.traverse_up(thread.parent)
        await super().traverse_up(thread)

    async def backup(self, thread: Thread) -> None:
        if not thread.parent:
            return

        log.debug('backing up thread %s', thread.name)
        entity: ThreadEntity = await self.mapper.map(thread)
        await self.repository.insert(entity)

    @inject.autoparams()
    async def traverse_down(self, thread: Thread, message_backup: Backup[discord.Message]) -> None:
        if not thread.parent:
            return

        await super().traverse_down(thread)

        async for message in await MessageIterator(thread).history():
            await message_backup.traverse_down(message)
