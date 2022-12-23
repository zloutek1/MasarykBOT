import logging

import inject
from discord import Role

from bot.db import RoleRepository, RoleMapper, RoleEntity
from ._base import Backup

log = logging.getLogger(__name__)


class RoleBackup(Backup[Role]):
    @inject.autoparams('role_repository', 'mapper')
    def __init__(self, role_repository: RoleRepository, mapper: RoleMapper) -> None:
        super().__init__()
        self.role_repository = role_repository
        self.mapper = mapper


    async def traverse_up(self, role: Role) -> None:
        from .guild import GuildBackup
        await GuildBackup().traverse_up(role.guild)
        await self.backup(role)


    async def backup(self, role: Role) -> None:
        log.debug("backing up role %s", role)
        entity: RoleEntity = await self.mapper.map(role)
        await self.role_repository.insert(entity)


    async def traverse_down(self, role: Role) -> None:
        await self.backup(role)
