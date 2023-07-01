import random
from typing import Optional, Tuple

import inject
from discord.utils import get

from src.bot import CONFIG
from src.bot import MarkovRepository, UnitOfWork, DBConnection

DEFAULT_CONTEXT_SIZE = 8


class MarkovGenerationService:
    @inject.autoparams('markov_repository', 'uow')
    def __init__(self, markov_repository: MarkovRepository, uow: UnitOfWork) -> None:
        self.markov_repository = markov_repository
        self.uow = uow

    async def generate(self, guild_id: int, start: str = '', limit: int = 4_000) -> str:
        async with self.uow.transaction(readonly=True) as transcation:
            (message, follows) = await self._try_to_find_start(guild_id, start, conn=transcation.conn)
            while follows is not None and len(message) < limit:
                message += follows
                follows = await self._find_next(guild_id, message, conn=transcation.conn)
            return message

    async def _try_to_find_start(self, guild_id: int, message: str, conn: DBConnection) -> Tuple[str, Optional[str]]:
        follows = await self._find_next(guild_id, message, conn)
        if not follows:
            message = ""
            follows = await self._find_next(guild_id, "", conn)
        return message, follows

    async def _find_next(self, guild_id: int, message: str, conn: DBConnection) -> Optional[str]:
        context_size = self._get_context_size(guild_id)
        if not (options := await self.markov_repository.find_random_next(guild_id, context=message[-context_size:], conn=conn)):
            return None

        follows = [option.follows for option in options]
        frequencies = [option.frequency for option in options]
        return random.choices(follows, weights=frequencies, k=1)[0]

    @staticmethod
    def _get_context_size(guild_id: int) -> int:
        if not (guild_config := get(CONFIG.guilds, id=guild_id)):
            return DEFAULT_CONTEXT_SIZE
        if not (markov_config := guild_config.cogs.markov):
            return DEFAULT_CONTEXT_SIZE
        return markov_config.context_size
