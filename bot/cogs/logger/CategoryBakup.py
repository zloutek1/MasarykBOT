import logging
import inject
from discord import CategoryChannel

from .Backup import Backup
import bot.db



log = logging.getLogger(__name__)



class CategoryBackup(Backup[CategoryChannel]):
    @inject.autoparams('categoryDao', 'mapper')
    def __init__(self, categoryDao: bot.db.CategoryRepository, mapper: bot.db.CategoryMapper) -> None:
        self.categoryDao = categoryDao
        self.mapper = mapper


    async def traverseUp(self, category: CategoryChannel) -> None:
        from .GuildBackup import GuildBackup
        await GuildBackup().traverseUp(category.guild)
        await super().traverseUp(category)


    async def backup(self, category: CategoryChannel) -> None:
        log.debug('backing up category %s', category.name)
        await super().backup(category)
        columns = await self.mapper.map(category)
        await self.categoryDao.insert([columns])


    async def traverseDown(self, category: CategoryChannel) -> None:
        from .TextChannelBackup import TextChannelBackup
        await super().traverseDown(category)
        
        for text_channel in category.text_channels:
            await TextChannelBackup().traverseDown(text_channel)