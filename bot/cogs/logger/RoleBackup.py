from discord import Role
import inject 

from .Backup import Backup
import bot.db

class RoleBackup(Backup[Role]):
    @inject.autoparams('roleRepository', 'mapper')
    def __init__(self, roleRepository: bot.db.RoleRepository, mapper: bot.db.RoleMapper) -> None:
        self.roleRepository = roleRepository
        self.mapper = mapper


    async def traverseUp(self, role: Role) -> None:
        from .GuildBackup import GuildBackup
        await GuildBackup().traverseUp(role.guild)
        await self.backup(role)


    async def backup(self, role: Role) -> None:
        print("backup role", role)
        columns = await self.mapper.map(role)
        await self.roleRepository.insert([columns])


    async def traverseDown(self, role: Role) -> None:
        await self.backup(role)