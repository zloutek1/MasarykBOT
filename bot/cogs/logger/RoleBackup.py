from discord import Role
import inject

from .Backup import Backup
import bot.db


class RoleBackup(Backup[Role]):
    @inject.autoparams('role_repository', 'mapper')
    def __init__(self, role_repository: bot.db.RoleRepository, mapper: bot.db.RoleMapper) -> None:
        self.role_repository = role_repository
        self.mapper = mapper

    async def traverse_up(self, role: Role) -> None:
        from .GuildBackup import GuildBackup
        await GuildBackup().traverse_up(role.guild)
        await self.backup(role)

    async def backup(self, role: Role) -> None:
        print("backup role", role)
        columns = await self.mapper.map(role)
        await self.role_repository.insert([columns])

    async def traverse_down(self, role: Role) -> None:
        await self.backup(role)
