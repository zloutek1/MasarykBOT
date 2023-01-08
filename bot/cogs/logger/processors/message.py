import asyncio
import logging

import discord
import inject
from discord import Message
from discord.ext import commands

from bot.db import MessageRepository, MessageMapper, MessageEntity, MessageEmojiMapper
from bot.utils import MessageEmote, MessageAttachment
from bot.cogs.logger.processors._base import Backup

log = logging.getLogger(__name__)



class MessageBackup(Backup[Message]):
    rate_limiter = 0


    @inject.autoparams()
    def __init__(
            self,
            bot: commands.Bot,
            message_repository: MessageRepository,
            mapper: MessageMapper,
            emoji_mapper: MessageEmojiMapper
    ) -> None:
        super().__init__()
        self.bot = bot
        self.message_repository = message_repository
        self.mapper = mapper
        self.emoji_mapper = emoji_mapper


    @inject.autoparams()
    async def traverse_up(
            self,
            message: Message,
            text_channel_backup: Backup[discord.TextChannel],
            user_backup: Backup[discord.User | discord.Member]
    ) -> None:
        if isinstance(message.channel, discord.TextChannel):
            await text_channel_backup.traverse_up(message.channel)
        await user_backup.traverse_up(message.author)
        await super().traverse_up(message)


    async def backup(self, message: Message) -> None:
        entity: MessageEntity = await self.mapper.map(message)
        await self.message_repository.insert(entity)

        self.bot.dispatch("message_backup", message)
        await self._prevent_rate_limit()


    @inject.autoparams()
    async def traverse_down(
            self,
            message: Message,
            reaction_backup: Backup[discord.Reaction],
            attachment_backup: Backup[MessageAttachment],
            message_emoji_backup: Backup[MessageEmote]
    ) -> None:
        await super().traverse_down(message)

        for reaction in message.reactions:
            await reaction_backup.traverse_down(reaction)

        for attachment in message.attachments:
            await attachment_backup.traverse_down(MessageAttachment(message, attachment))

        for emoji in await self.emoji_mapper.map_emojis(self.bot, message):
            await message_emoji_backup.traverse_down(emoji)


    async def _prevent_rate_limit(self) -> None:
        self.rate_limiter += 1
        if self.rate_limiter > 8_000:
            log.info('sleeping for 8 minutes to reduce rate limit')
            await asyncio.sleep(60 * 8)
            self.rate_limiter = 0
