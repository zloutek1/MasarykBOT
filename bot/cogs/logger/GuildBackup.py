import logging

import inject
from discord import Guild

from .Backup import Backup
import bot.db

log = logging.getLogger(__name__)


class GuildBackup(Backup[Guild]):
    @inject.autoparams('guild_repository', 'mapper')
    def __init__(self, guild_repository: bot.db.GuildRepository, mapper: bot.db.GuildMapper) -> None:
        self.guild_repository = guild_repository
        self.mapper = mapper

    async def traverse_up(self, guild: Guild) -> None:
        await super().traverse_up(guild)

    async def backup(self, guild: Guild) -> None:
        log.debug('backing up guild %s', guild.name)
        await super().backup(guild)
        columns = await self.mapper.map(guild)
        await self.guild_repository.insert([columns])

    async def traverse_down(self, guild: Guild) -> None:
        await super().traverse_down(guild)

        from .UserBackup import UserBackup
        for user in guild.members:
            await UserBackup().traverse_down(user)

        from .RoleBackup import RoleBackup
        for role in guild.roles:
            await RoleBackup().traverse_down(role)

        from .EmojiBackup import EmojiBackup
        for emoji in guild.emojis:
            await EmojiBackup().traverse_down(emoji)

        from .TextChannelBackup import TextChannelBackup
        for text_channel in filter(lambda ch: ch.category is None, guild.text_channels):
            await TextChannelBackup().traverse_down(text_channel)

        from .CategoryBakup import CategoryBackup
        for category in guild.categories:
            await CategoryBackup().traverse_down(category)
