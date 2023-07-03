import abc
from typing import Generic, TypeVar, Self

from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped

from core.dated.mixin import DatedMixin

T = TypeVar('T')


class DiscordMixin(DatedMixin, Generic[T]):
    discord_id: Mapped[str] = Column(String, nullable=False)

    @classmethod
    @abc.abstractmethod
    def from_discord(cls, dto: T) -> Self:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.discord_id == self.discord_id
        return False

    def __hash__(self) -> int:
        return hash(self.discord_id)
