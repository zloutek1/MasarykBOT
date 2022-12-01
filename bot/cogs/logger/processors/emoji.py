import logging

import inject
from discord import Emoji, PartialEmoji

from bot.db import EmojiRepository, EmojiMapper, EmojiEntity
from ._base import Backup

log = logging.getLogger(__name__)


class EmojiBackup(Backup[Emoji | PartialEmoji | str]):
    @inject.autoparams('emoji_repository', 'mapper')
    def __init__(self, emoji_repository: EmojiRepository, mapper: EmojiMapper) -> None:
        self.emoji_repository = emoji_repository
        self.mapper = mapper

    async def traverse_up(self, emoji: Emoji | PartialEmoji | str) -> None:
        if isinstance(emoji, Emoji) and emoji.guild:
            from .guild import GuildBackup
            await GuildBackup().traverse_up(emoji.guild)
        await super().traverse_up(emoji)

    async def backup(self, emoji: Emoji | PartialEmoji | str) -> None:
        log.debug('backing up emoji %s', emoji.name if hasattr(emoji, 'name') else emoji)
        await super().backup(emoji)
        entity: EmojiEntity = await self.mapper.map(emoji)
        await self.emoji_repository.insert([entity])

    async def traverse_down(self, emoji: Emoji | PartialEmoji | str) -> None:
        await super().traverse_down(emoji)
