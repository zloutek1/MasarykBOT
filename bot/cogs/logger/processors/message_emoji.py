from typing import Tuple
import inject

from discord import Message
from discord.ext import commands

from bot.db.discord import MessageEmojiEntity, MessageEmojiMapper, MessageEmojiRepository
from ._base import Backup



class MessageEmojiBackup(Backup[Message]):
    @inject.autoparams('bot', 'repository', 'mapper')
    def __init__(self, bot: commands.Bot, repository: MessageEmojiRepository, mapper: MessageEmojiMapper) -> None:
        super().__init__()
        self.bot = bot
        self.repository = repository
        self.mapper = mapper


    async def traverse_up(self, message: Message) -> None:
        from .emoji import EmojiBackup
        for emoji in await self.mapper.map_emojis(self.bot, message):
            await EmojiBackup().traverse_up(emoji)

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
