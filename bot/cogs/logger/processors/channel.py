import logging

import discord
import inject
from discord.abc import GuildChannel

from bot.cogs.logger.message_iterator import MessageIterator
from bot.cogs.logger.processors._base import Backup
from bot.db import ChannelRepository, ChannelMapper, ChannelEntity

log = logging.getLogger(__name__)


class ChannelBackup(Backup[GuildChannel]):
    @inject.autoparams()
    def __init__(self, channel_repository: ChannelRepository, mapper: ChannelMapper) -> None:
        super().__init__()
        self.channel_repository = channel_repository
        self.mapper = mapper

    @inject.autoparams()
    async def traverse_up(
        self,
        channel: GuildChannel,
        category_backup: Backup[discord.CategoryChannel],
        guild_backup: Backup[discord.Guild]
    ) -> None:
        if not self.mapper.can_map(channel):
            return

        if channel.category:
            await category_backup.traverse_up(channel.category)
        else:
            await guild_backup.traverse_up(channel.guild)
        await super().traverse_up(channel)

    async def backup(self, channel: GuildChannel) -> None:
        if not self.mapper.can_map(channel):
            return

        log.debug('backing up channel %s', channel.name)
        entity: ChannelEntity = await self.mapper.map(channel)
        await self.channel_repository.insert(entity)

    @inject.autoparams()
    async def traverse_down(
        self,
        channel: GuildChannel,
        message_backup: Backup[discord.Message],
        thread_backup: Backup[discord.Thread]
    ) -> None:
        if not self.mapper.can_map(channel):
            return

        if channel.name != "threader":
            return

        await super().traverse_down(channel)

        if isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
            for thread in channel.threads:
                await thread_backup.traverse_down(thread)
            async for thread in channel.archived_threads(limit=None):
                await thread_backup.traverse_down(thread)

        async for message in await MessageIterator(channel).history():
            await message_backup.traverse_down(message)
