import logging

import discord
import inject
from discord import TextChannel
from discord.abc import GuildChannel

from bot.db import ChannelRepository, ChannelMapper, ChannelEntity
from bot.cogs.logger.processors._base import Backup
from ..message_iterator import MessageIterator

log = logging.getLogger(__name__)


class TextChannelBackup(Backup[TextChannel]):
    @inject.autoparams()
    def __init__(self, channel_repository: ChannelRepository, mapper: ChannelMapper) -> None:
        super().__init__()
        self.channel_repository = channel_repository
        self.mapper = mapper


    @inject.autoparams()
    async def traverse_up(
            self,
            text_channel: TextChannel,
            category_backup: Backup[discord.CategoryChannel],
            guild_backup: Backup[discord.Guild]
    ) -> None:
        if isinstance(text_channel, GuildChannel):
            if text_channel.category:
                await category_backup.traverse_up(text_channel.category)
            else:
                await guild_backup.traverse_up(text_channel.guild)
        await super().traverse_up(text_channel)


    async def backup(self, text_channel: TextChannel) -> None:
        log.debug('backing up text channel %s', text_channel.name)
        entity: ChannelEntity = await self.mapper.map(text_channel)
        await self.channel_repository.insert(entity)


    @inject.autoparams()
    async def traverse_down(self, text_channel: TextChannel, message_backup: Backup[discord.Message]) -> None:
        await super().traverse_down(text_channel)

        async for message in await MessageIterator(text_channel).history():
            await message_backup.traverse_down(message)
