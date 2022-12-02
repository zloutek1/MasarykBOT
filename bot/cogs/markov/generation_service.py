import random
from typing import Optional

import inject

from bot.db.cogs import MarkovRepository


CONTEXT_SIZE = 8


class MarkovGenerationService:
    @inject.autoparams('markov_repository')
    def __init__(self, markov_repository: MarkovRepository) -> None:
        self.markov_repository = markov_repository


    async def generate(self, guild_id: int, start: str = 0, limit: int = 4_000) -> str:
        (message, follows) = await self._try_to_find_start(guild_id, start)
        while follows is not None and len(message) < limit:
            message += follows
            follows = await self._find_next(guild_id, message)
        return message


    async def _try_to_find_start(self, guild_id: int, message: str) -> (str, str):
        follows = await self._find_next(guild_id, message)
        if not follows:
            message = ""
            follows = await self.markov_repository.find_random_next(guild_id, context="")
        return message, follows


    async def _find_next(self, guild_id: int, message: str) -> Optional[str]:
        if not (options := await self.markov_repository.find_random_next(guild_id, context=message[-CONTEXT_SIZE:])):
            return None

        follows = [option.follows for option in options]
        frequencies = [option.frequency for option in options]
        return random.choices(follows, weights=frequencies, k=1)[0]
