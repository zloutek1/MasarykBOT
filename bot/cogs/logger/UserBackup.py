import logging

import inject
from discord import User, Member

from bot.cogs.logger.Backup import Backup
import bot.db



log = logging.getLogger(__name__)



class UserBackup(Backup[User | Member]):
    @inject.autoparams('userRepository', 'mapper')
    def __init__(self, userRepository: bot.db.UserRepository, mapper: bot.db.UserMapper) -> None:
        self.userRepository = userRepository
        self.mapper = mapper


    async def traverseUp(self, user: User | Member) -> None:
        from .GuildBackup import GuildBackup
        if isinstance(user, Member):
            await GuildBackup().traverseUp(user.guild)
        await super().traverseUp(user)


    async def backup(self, user: User | Member) -> None:
        log.debug('backing up user %s', user.name)
        await super().backup(user)
        columns = await self.mapper.map(user)
        await self.userRepository.insert([columns])


    async def traverseDown(self, user: User | Member) -> None:
        await super().traverseDown(user)