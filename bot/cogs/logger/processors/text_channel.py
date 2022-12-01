import logging

import inject
from discord import TextChannel
from discord.abc import GuildChannel

from bot.db import ChannelRepository, ChannelMapper, ChannelEntity
from ._base import Backup
from .message import MessageBackup
from ..message_iterator import MessageIterator

log = logging.getLogger(__name__)


class TextChannelBackup(Backup[TextChannel]):
    @inject.autoparams('channel_repository', 'mapper')
    def __init__(self, channel_repository: ChannelRepository, mapper: ChannelMapper) -> None:
        self.channel_repository = channel_repository
        self.mapper = mapper

    async def traverse_up(self, text_channel: TextChannel) -> None:
        if isinstance(text_channel, GuildChannel):
            if text_channel.category:
                from .category import CategoryBackup
                await CategoryBackup().traverse_up(text_channel.category)
            else:
                from .guild import GuildBackup
                await GuildBackup().traverse_up(text_channel.guild)

        await super().traverse_up(text_channel)

    async def backup(self, text_channel: TextChannel) -> None:
        log.debug('backing up text channel %s', text_channel.name)
        await super().backup(text_channel)
        entity: ChannelEntity = await self.mapper.map(text_channel)
        await self.channel_repository.insert([entity])

    async def traverse_down(self, text_channel: TextChannel) -> None:
        await super().traverse_down(text_channel)

        async for message in await MessageIterator(text_channel).history():
            await MessageBackup().traverse_down(message)
