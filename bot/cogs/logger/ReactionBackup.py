import inject
from discord import Reaction

from .Backup import Backup
import bot.db


class ReactionBackup(Backup[Reaction]):
    @inject.autoparams('reaction_repository', 'mapper')
    def __init__(self, reaction_repository: bot.db.ReactionRepository, mapper: bot.db.ReactionMapper) -> None:
        self.reaction_repository = reaction_repository
        self.mapper = mapper

    async def traverse_up(self, reaction: Reaction) -> None:
        from .EmojiBackup import EmojiBackup
        await EmojiBackup().traverse_up(reaction.emoji)

        from .MessageBackup import MessageBackup
        await MessageBackup().traverse_up(reaction.message)

        await super().traverse_up(reaction)

    async def backup(self, reaction: Reaction) -> None:
        await super().backup(reaction)
        columns = await self.mapper.map(reaction)
        await self.reaction_repository.insert([columns])

    async def traverse_down(self, reaction: Reaction) -> None:
        await super().traverse_down(reaction)
