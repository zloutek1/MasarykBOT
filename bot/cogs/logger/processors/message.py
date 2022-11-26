import asyncio
import logging

import inject
from discord import Message

from ._base import Backup
import bot.db

log = logging.getLogger(__name__)


class MessageBackup(Backup[Message]):
    rate_limiter = 0

    @inject.autoparams('message_repository', 'mapper')
    def __init__(self, message_repository: bot.db.MessageRepository, mapper: bot.db.MessageMapper) -> None:
        self.message_repository = message_repository
        self.mapper = mapper

    async def traverse_up(self, message: Message) -> None:
        from .text_channel import TextChannelBackup
        await TextChannelBackup().traverse_up(message.channel)

        from .user import UserBackup
        await UserBackup().traverse_up(message.author)

        await super().traverse_up(message)

    async def backup(self, message: Message) -> None:
        await super().backup(message)
        columns = await self.mapper.map(message)
        await self.message_repository.insert([columns])

        self.rate_limiter += 1
        if self.rate_limiter > 8_000:
            log.info('sleeping for 8 minutes to reduce rate limit')
            await asyncio.sleep(60 * 8)
            self.rate_limiter = 0

    async def traverse_down(self, message: Message) -> None:
        await super().traverse_down(message)

        from .reaction import ReactionBackup
        for reaction in message.reactions:
            await ReactionBackup().traverse_down(reaction)

        from .attachment import AttachmentBackup
        for attachment in message.attachments:
            await AttachmentBackup(message.id).traverse_down(attachment)
