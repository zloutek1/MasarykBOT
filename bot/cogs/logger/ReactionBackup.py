import inject
from discord import Reaction

from .Backup import Backup
import bot.db



class ReactionBackup(Backup[Reaction]):
    @inject.autoparams('reactionRepository', 'mapper')
    def __init__(self, reactionRepository: bot.db.ReactionRepository, mapper: bot.db.ReactionMapper) -> None:
        self.reactionRepository = reactionRepository
        self.mapper = mapper


    async def traverseUp(self, reaction: Reaction) -> None:
        from .EmojiBackup import EmojiBackup
        await EmojiBackup().traverseUp(reaction.emoji)

        from .MessageBackup import MessageBackup
        await MessageBackup().traverseUp(reaction.message)

        await super().traverseUp(reaction)


    async def backup(self, reaction: Reaction) -> None:
        await super().backup(reaction)
        columns = await self.mapper.map(reaction)
        await self.reactionRepository.insert([columns])


    async def traverseDown(self, reaction: Reaction) -> None:
        await super().traverseDown(reaction)
