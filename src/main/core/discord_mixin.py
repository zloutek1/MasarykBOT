import abc
from dataclasses import dataclass
from typing import Generic, TypeVar, Self

from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped

T = TypeVar('T')


@dataclass
class DiscordMixin(abc.ABC, Generic[T]):
    discord_id: Mapped[str] = Column(String, nullable=False)

    @classmethod
    @abc.abstractmethod
    def from_discord(cls, dto: T) -> Self:
        raise NotImplementedError
