import logging

import inject
from discord import Emoji, PartialEmoji

from .Backup import Backup
import bot.db



log = logging.getLogger(__name__)



class EmojiBackup(Backup[Emoji | PartialEmoji | str]):
    @inject.autoparams('emojiRepository', 'mapper')
    def __init__(self, emojiRepository: bot.db.EmojiRepository, mapper: bot.db.EmojiMapper) -> None:
        self.emojiRepository = emojiRepository
        self.mapper = mapper


    async def traverseUp(self, emoji: Emoji | PartialEmoji | str) -> None:
        if isinstance(emoji, Emoji) and emoji.guild:
            from .GuildBackup import GuildBackup
            await GuildBackup().traverseUp(emoji.guild)
        await super().traverseUp(emoji)


    async def backup(self, emoji: Emoji | PartialEmoji | str) -> None:
        log.debug('backing up emoji %s', emoji.name if hasattr(emoji, 'name') else emoji)
        await super().backup(emoji)
        columns = await self.mapper.map(emoji)
        await self.emojiRepository.insert([columns])


    async def traverseDown(self, emoji: Emoji | PartialEmoji | str) -> None:
        await super().traverseDown(emoji)