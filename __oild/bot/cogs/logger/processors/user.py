import logging

import discord
import inject
from discord import User, Member

from src.bot import UserRepository, UserMapper, UserEntity
from . import Backup

log = logging.getLogger(__name__)


class UserBackup(Backup[User | Member]):
    @inject.autoparams()
    def __init__(self, user_repository: UserRepository, mapper: UserMapper) -> None:
        super().__init__()
        self.user_repository = user_repository
        self.mapper = mapper

    @inject.autoparams()
    async def traverse_up(self, user: User | Member, guild_backup: Backup[discord.Guild]) -> None:
        if isinstance(user, Member):
            await guild_backup.traverse_up(user.guild)
        await super().traverse_up(user)

    async def backup(self, user: User | Member) -> None:
        log.debug('backing up user %s', user.name)
        entity: UserEntity = await self.mapper.map(user)
        await self.user_repository.insert(entity)

    async def traverse_down(self, user: User | Member) -> None:
        await super().traverse_down(user)
