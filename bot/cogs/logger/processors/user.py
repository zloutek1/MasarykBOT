import logging

import inject
from discord import User, Member

from bot.db import UserRepository, UserMapper, UserEntity
from ._base import Backup

log = logging.getLogger(__name__)


class UserBackup(Backup[User | Member]):
    @inject.autoparams('user_repository', 'mapper')
    def __init__(self, user_repository: UserRepository, mapper: UserMapper) -> None:
        self.user_repository = user_repository
        self.mapper = mapper

    async def traverse_up(self, user: User | Member) -> None:
        from .guild import GuildBackup
        if isinstance(user, Member):
            await GuildBackup().traverse_up(user.guild)
        await super().traverse_up(user)

    async def backup(self, user: User | Member) -> None:
        log.debug('backing up user %s', user.name)
        await super().backup(user)
        entity: UserEntity = await self.mapper.map(user)
        await self.user_repository.insert([entity])

    async def traverse_down(self, user: User | Member) -> None:
        await super().traverse_down(user)
