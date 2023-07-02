from typing import Type

from core.dated.repository import DatedRepository
from guild.model import Guild

__all__ = ["GuildRepository"]


class GuildRepository(DatedRepository[Guild]):
    @property
    def model(self) -> Type:
        return Guild
