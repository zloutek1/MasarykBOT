from typing import Tuple
import inject

from discord import Message
from bot.db.discord import MessageEmojiEntity, MessageEmojiMapper, MessageEmojiRepository

from ._base import Backup



class MessageEmojiBackup(Backup[Message]):
    @inject.autoparams('repository', 'mapper')
    def __init__(
            self,
            repository: MessageEmojiRepository,
            mapper: MessageEmojiMapper
    ) -> None:
        self.repository = repository
        self.mapper = mapper


    async def traverse_up(self, message: Message) -> None:
        from .message import MessageBackup
        await MessageBackup().traverse_up(message)

        await super().traverse_up(message)


    async def backup(self, message: Message) -> None:
        await super().backup(message)

        entities: Tuple[MessageEmojiEntity, ...] = await self.mapper.map(message)
        for entity in entities:
            await self.repository.insert(entity)


    async def traverse_down(self, message: Message) -> None:
        await super().traverse_down(message)
