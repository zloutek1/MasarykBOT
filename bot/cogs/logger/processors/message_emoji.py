import logging

import discord
import inject
from discord.ext import commands

from bot.cogs.logger.processors._base import Backup
from bot.db.discord import MessageEmojiEntity, MessageEmojiMapper, MessageEmojiRepository
from bot.utils import MessageEmote, AnyEmote

log = logging.getLogger(__name__)


class MessageEmojiBackup(Backup[MessageEmote]):
    @inject.autoparams()
    def __init__(self, bot: commands.Bot, repository: MessageEmojiRepository, mapper: MessageEmojiMapper) -> None:
        super().__init__()
        self.bot = bot
        self.repository = repository
        self.mapper = mapper

    @inject.autoparams()
    async def traverse_up(
        self,
        message_emoji: MessageEmote,
        message_backup: Backup[discord.Message],
        emoji_backup: Backup[AnyEmote]
    ) -> None:
        await message_backup.traverse_up(message_emoji.message)
        await emoji_backup.traverse_up(message_emoji.emoji)
        await super().traverse_up(message_emoji)

    async def backup(self, emoji: MessageEmote) -> None:
        log.debug("Backung up message_emoji %s", emoji.emoji)

        entity: MessageEmojiEntity = await self.mapper.map(emoji)
        await self.repository.insert(entity)

    async def traverse_down(self, emoji: MessageEmote) -> None:
        await super().traverse_down(emoji)
