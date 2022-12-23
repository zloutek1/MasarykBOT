import logging

import inject
from discord import CategoryChannel

from bot.db import CategoryMapper, CategoryRepository, CategoryEntity
from ._base import Backup

log = logging.getLogger(__name__)


class CategoryBackup(Backup[CategoryChannel]):
    @inject.autoparams('category_repository', 'mapper')
    def __init__(self, category_repository: CategoryRepository, mapper: CategoryMapper) -> None:
        super().__init__()
        self.category_repository = category_repository
        self.mapper = mapper


    async def traverse_up(self, category: CategoryChannel) -> None:
        from .guild import GuildBackup
        await GuildBackup().traverse_up(category.guild)
        await super().traverse_up(category)


    async def backup(self, category: CategoryChannel) -> None:
        log.debug('backing up category %s', category.name)
        await super().backup(category)
        entity: CategoryEntity = await self.mapper.map(category)
        await self.category_repository.insert(entity)


    async def traverse_down(self, category: CategoryChannel) -> None:
        from .text_channel import TextChannelBackup
        await super().traverse_down(category)

        for text_channel in category.text_channels:
            await TextChannelBackup().traverse_down(text_channel)
