import logging

import discord
import inject
from discord import Guild

from src.bot import GuildRepository, GuildMapper, GuildEntity
from src.bot import AnyEmote
from . import Backup

log = logging.getLogger(__name__)


class GuildBackup(Backup[Guild]):
    @inject.autoparams()
    def __init__(self, guild_repository: GuildRepository, mapper: GuildMapper) -> None:
        super().__init__()
        self.guild_repository = guild_repository
        self.mapper = mapper

    async def traverse_up(self, guild: Guild) -> None:
        await super().traverse_up(guild)

    async def backup(self, guild: Guild) -> None:
        log.debug('backing up guild %s', guild.name)
        entity: GuildEntity = await self.mapper.map(guild)
        await self.guild_repository.insert(entity)

    @inject.autoparams()
    async def traverse_down(
            self,
            guild: Guild,
            user_backup: Backup[discord.User | discord.Member],
            role_backup: Backup[discord.Role],
            emoji_backup: Backup[AnyEmote],
            channel_backup: Backup[discord.abc.GuildChannel],
            category_backup: Backup[discord.CategoryChannel]
    ) -> None:
        await super().traverse_down(guild)

        for user in guild.members:
            await user_backup.traverse_down(user)

        for role in guild.roles:
            await role_backup.traverse_down(role)

        for emoji in guild.emojis:
            await emoji_backup.traverse_down(emoji)

        for channel in filter(lambda ch: ch.category is None, guild.channels):
            await channel_backup.traverse_down(channel)

        for category in guild.categories:
            await category_backup.traverse_down(category)
