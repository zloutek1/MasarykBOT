import logging

import inject
from discord import Guild

from .Backup import Backup
import bot.db



log = logging.getLogger(__name__)



class GuildBackup(Backup[Guild]):
    @inject.autoparams('guildRepository', 'mapper')
    def __init__(self, guildRepository: bot.db.GuildRepository, mapper: bot.db.GuildMapper) -> None:
        self.guildRepository = guildRepository
        self.mapper = mapper


    async def traverseUp(self, guild: Guild) -> None:
        await super().traverseUp(guild)


    async def backup(self, guild: Guild) -> None:
        log.debug('backing up guild %s', guild.name)
        await super().backup(guild)
        columns = await self.mapper.map(guild)
        await self.guildRepository.insert([columns])


    async def traverseDown(self, guild: Guild) -> None:
        await super().traverseDown(guild)

        from .UserBackup import UserBackup
        for user in guild.members:
            await UserBackup().traverseDown(user)
        
        from .RoleBackup import RoleBackup
        for role in guild.roles:
            await RoleBackup().traverseDown(role)

        from .EmojiBackup import EmojiBackup
        for emoji in guild.emojis:
            await EmojiBackup().traverseDown(emoji)

        from .TextChannelBackup import TextChannelBackup
        for text_channel in filter(lambda ch: ch.category is None, guild.text_channels):
            await TextChannelBackup().traverseDown(text_channel)

        from .CategoryBakup import CategoryBackup        
        for category in guild.categories:
            await CategoryBackup().traverseDown(category)
