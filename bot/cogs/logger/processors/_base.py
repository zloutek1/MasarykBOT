from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Type

T = TypeVar('T')
R = TypeVar('R')


class Backup(ABC, Generic[T]):
    _backedUp: dict[Type["Backup"], set[T]] = {}

    def __init__(self):
        self._backedUp.setdefault(type(self), set())

    @abstractmethod
    async def traverse_up(self, obj: T) -> None:
        if obj in self._backedUp[type(self)]:
            return
        await self.backup(obj)


    @abstractmethod
    async def backup(self, obj: T) -> None:
        self._backedUp[type(self)].add(obj)


    @abstractmethod
    async def traverse_down(self, obj: T) -> None:
        await self.traverse_up(obj)
