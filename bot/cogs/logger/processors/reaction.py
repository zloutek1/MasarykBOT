import discord
import inject
from discord import Reaction

from bot.db import ReactionRepository, ReactionMapper, ReactionEntity
from bot.utils import AnyEmote
from ._base import Backup



class ReactionBackup(Backup[Reaction]):
    @inject.autoparams()
    def __init__(self, reaction_repository: ReactionRepository, mapper: ReactionMapper) -> None:
        super().__init__()
        self.reaction_repository = reaction_repository
        self.mapper = mapper


    @inject.autoparams()
    async def traverse_up(
            self,
            reaction: Reaction,
            emoji_backup: Backup[AnyEmote],
            message_backup: Backup[discord.Message]
    ) -> None:
        await emoji_backup.traverse_up(reaction.emoji)
        await message_backup.traverse_up(reaction.message)
        await super().traverse_up(reaction)


    async def backup(self, reaction: Reaction) -> None:
        entity: ReactionEntity = await self.mapper.map(reaction)
        await self.reaction_repository.insert(entity)


    async def traverse_down(self, reaction: Reaction) -> None:
        await super().traverse_down(reaction)
