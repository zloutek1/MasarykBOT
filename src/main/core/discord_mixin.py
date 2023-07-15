import abc
from typing import Generic, TypeVar, Self

from discord.types.snowflake import Snowflake
from sqlalchemy import Column, Integer
from sqlalchemy.orm import Mapped

from core.dated.mixin import DatedMixin

T = TypeVar('T')


class DiscordMixin(DatedMixin, Generic[T]):
    """
    An addition to the Entity class
    provides the database entity with a discord_id and logic based on that
    """

    discord_id: Mapped[Snowflake] = Column(Integer, nullable=False)

    @classmethod
    @abc.abstractmethod
    def from_discord(cls, dto: T) -> Self:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.discord_id == other.discord_id
        return False

    def __hash__(self) -> int:
        return int(self.discord_id)
