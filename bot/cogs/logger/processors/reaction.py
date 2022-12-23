import inject
from discord import Reaction

from bot.db import ReactionRepository, ReactionMapper, ReactionEntity
from ._base import Backup



class ReactionBackup(Backup[Reaction]):
    @inject.autoparams('reaction_repository', 'mapper')
    def __init__(self, reaction_repository: ReactionRepository, mapper: ReactionMapper) -> None:
        super().__init__()
        self.reaction_repository = reaction_repository
        self.mapper = mapper


    async def traverse_up(self, reaction: Reaction) -> None:
        from .emoji import EmojiBackup
        await EmojiBackup().traverse_up(reaction.emoji)

        from .message import MessageBackup
        await MessageBackup().traverse_up(reaction.message)

        await super().traverse_up(reaction)


    async def backup(self, reaction: Reaction) -> None:
        await super().backup(reaction)
        entity: ReactionEntity = await self.mapper.map(reaction)
        await self.reaction_repository.insert(entity)


    async def traverse_down(self, reaction: Reaction) -> None:
        await super().traverse_down(reaction)
