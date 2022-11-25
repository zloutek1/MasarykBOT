import logging

import inject
from discord import Message

from .Backup import Backup
import bot.db



class MessageBackup(Backup[Message]):
    @inject.autoparams('messageRepository', 'mapper')
    def __init__(self, messageRepository: bot.db.MessageRepository, mapper: bot.db.MessageMapper) -> None:
        self.messageRepository = messageRepository
        self.mapper = mapper


    async def traverseUp(self, message: Message) -> None:
        from .TextChannelBackup import TextChannelBackup
        await TextChannelBackup().traverseUp(message.channel)

        from .UserBackup import UserBackup
        await UserBackup().traverseUp(message.author)

        await super().traverseUp(message)


    async def backup(self, message: Message) -> None:
        await super().backup(message)
        columns = await self.mapper.map(message)
        await self.messageRepository.insert([columns])


    async def traverseDown(self, message: Message) -> None:
        await super().traverseDown(message)

        from .ReactionBackup import ReactionBackup
        for reaction in message.reactions:
            await ReactionBackup().traverseDown(reaction)

        from .AttachmentBackup import AttachmentBackup
        for attachment in message.attachments:
            await AttachmentBackup(message.id).traverseDown(attachment)