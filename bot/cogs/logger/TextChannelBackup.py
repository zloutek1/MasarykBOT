import logging

import inject
from discord import TextChannel
from discord.abc import GuildChannel

from .Backup import Backup
from .MessageIterator import MessageIterator
from .MessageBackup import MessageBackup
import bot.db



log = logging.getLogger(__name__)



class TextChannelBackup(Backup[TextChannel]):
    @inject.autoparams('channelRepository', 'mapper')
    def __init__(self, channelRepository: bot.db.ChannelRepository, mapper: bot.db.ChannelMapper) -> None:
        self.channelRepository = channelRepository
        self.mapper = mapper


    async def traverseUp(self, text_channel: TextChannel) -> None:
        if isinstance(text_channel, GuildChannel):
            if text_channel.category:
                from .CategoryBakup import CategoryBackup
                await CategoryBackup().traverseUp(text_channel.category)
            else:
                from .GuildBackup import GuildBackup
                await GuildBackup().traverseUp(text_channel.guild)

        await super().traverseUp(text_channel)


    async def backup(self, text_channel: TextChannel) -> None:
        log.debug('backing up text channel %s', text_channel.name)
        await super().backup(text_channel)
        columns = await self.mapper.map(text_channel)
        await self.channelRepository.insert([columns])


    async def traverseDown(self, text_channel: TextChannel) -> None:
        await super().traverseDown(text_channel)

        async for message in await MessageIterator(text_channel).history():
            await MessageBackup().traverseDown(message)