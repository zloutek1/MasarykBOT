import logging

import discord
import inject
from discord import CategoryChannel

from bot.db import CategoryMapper, CategoryRepository, CategoryEntity
from ._base import Backup

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
    async def traverse_down(self, category: CategoryChannel, text_channel_backup: Backup[discord.TextChannel]) -> None:
        await super().traverse_down(category)

        for text_channel in category.text_channels:
            await text_channel_backup.traverse_down(text_channel)
