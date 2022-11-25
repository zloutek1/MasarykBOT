import logging

import inject
from discord import Message

from .Backup import Backup
import bot.db


class MessageBackup(Backup[Message]):
    @inject.autoparams('message_repository', 'mapper')
    def __init__(self, message_repository: bot.db.MessageRepository, mapper: bot.db.MessageMapper) -> None:
        self.message_repository = message_repository
        self.mapper = mapper

    async def traverse_up(self, message: Message) -> None:
        from .TextChannelBackup import TextChannelBackup
        await TextChannelBackup().traverse_up(message.channel)

        from .UserBackup import UserBackup
        await UserBackup().traverse_up(message.author)

        await super().traverse_up(message)

    async def backup(self, message: Message) -> None:
        await super().backup(message)
        columns = await self.mapper.map(message)
        await self.message_repository.insert([columns])

    async def traverse_down(self, message: Message) -> None:
        await super().traverse_down(message)

        from .ReactionBackup import ReactionBackup
        for reaction in message.reactions:
            await ReactionBackup().traverse_down(reaction)

        from .AttachmentBackup import AttachmentBackup
        for attachment in message.attachments:
            await AttachmentBackup(message.id).traverse_down(attachment)
