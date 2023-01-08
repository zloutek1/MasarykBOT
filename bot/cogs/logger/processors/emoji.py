import logging

import discord
import inject
from discord import Emoji

from bot.cogs.logger.processors._base import Backup
from bot.db import EmojiRepository, EmojiMapper, EmojiEntity
from bot.utils import AnyEmote

log = logging.getLogger(__name__)


class EmojiBackup(Backup[AnyEmote]):
    @inject.autoparams()
    def __init__(self, emoji_repository: EmojiRepository, mapper: EmojiMapper) -> None:
        super().__init__()
        self.emoji_repository = emoji_repository
        self.mapper = mapper


    @inject.autoparams()
    async def traverse_up(self, emoji: AnyEmote, guild_backup: Backup[discord.Guild]) -> None:
        if isinstance(emoji, Emoji) and emoji.guild:
            await guild_backup.traverse_up(emoji.guild)
        await super().traverse_up(emoji)


    async def backup(self, emoji: AnyEmote) -> None:
        log.debug('backing up emoji %s', emoji.name if hasattr(emoji, 'name') else emoji)
        entity: EmojiEntity = await self.mapper.map(emoji)
        await self.emoji_repository.insert(entity)


    async def traverse_down(self, emoji: AnyEmote) -> None:
        await super().traverse_down(emoji)
