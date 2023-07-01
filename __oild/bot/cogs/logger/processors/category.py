import logging

import discord
import inject
from discord import CategoryChannel

from src.bot import CategoryMapper, CategoryRepository, CategoryEntity
from __oild.bot.cogs.logger.processors._base import Backup

log = logging.getLogger(__name__)


class CategoryBackup(Backup[CategoryChannel]):
    @inject.autoparams()
    def __init__(self, category_repository: CategoryRepository, mapper: CategoryMapper) -> None:
        super().__init__()
        self.category_repository = category_repository
        self.mapper = mapper

    @inject.autoparams()
    async def traverse_up(self, category: CategoryChannel, guild_backup: Backup[discord.Guild]) -> None:
        await guild_backup.traverse_up(category.guild)
        await super().traverse_up(category)

    async def backup(self, category: CategoryChannel) -> None:
        log.debug('backing up category %s', category.name)
        entity: CategoryEntity = await self.mapper.map(category)
        await self.category_repository.insert(entity)

    @inject.autoparams()
    async def traverse_down(self, category: CategoryChannel, channel_backup: Backup[discord.abc.GuildChannel]) -> None:
        await super().traverse_down(category)

        for channel in category.channels:
            await channel_backup.traverse_down(channel)
