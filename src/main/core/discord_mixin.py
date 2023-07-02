import abc
from dataclasses import dataclass
from typing import Generic, TypeVar, Self

from sqlalchemy import Column, String

T = TypeVar('T')


@dataclass
class DiscordMixin(abc.ABC, Generic[T]):
    discord_id: str = Column(String, nullable=False)

    @classmethod
    @abc.abstractmethod
    def from_discord(cls, dto: T) -> Self:
        raise NotImplementedError
