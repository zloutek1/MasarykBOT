import logging
import inject
from discord import CategoryChannel

from .Backup import Backup
import bot.db

log = logging.getLogger(__name__)


class CategoryBackup(Backup[CategoryChannel]):
    @inject.autoparams('category_repository', 'mapper')
    def __init__(self, category_repository: bot.db.CategoryRepository, mapper: bot.db.CategoryMapper) -> None:
        self.category_repository = category_repository
        self.mapper = mapper

    async def traverse_up(self, category: CategoryChannel) -> None:
        from .GuildBackup import GuildBackup
        await GuildBackup().traverse_up(category.guild)
        await super().traverse_up(category)

    async def backup(self, category: CategoryChannel) -> None:
        log.debug('backing up category %s', category.name)
        await super().backup(category)
        columns = await self.mapper.map(category)
        await self.category_repository.insert([columns])

    async def traverse_down(self, category: CategoryChannel) -> None:
        from .TextChannelBackup import TextChannelBackup
        await super().traverse_down(category)

        for text_channel in category.text_channels:
            await TextChannelBackup().traverse_down(text_channel)
