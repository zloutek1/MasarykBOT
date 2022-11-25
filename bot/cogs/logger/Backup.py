from abc import ABC, abstractmethod
from typing import Generic, TypeVar


T = TypeVar('T')
R = TypeVar('R')



class Backup(ABC, Generic[T]):
    _backedUp: set[T] = set()

    @abstractmethod
    async def traverseUp(self, obj: T) -> None:
        if obj in self._backedUp:
            return
        await self.backup(obj)

    @abstractmethod
    async def backup(self, obj: T) -> None:
        self._backedUp.add(obj)

    @abstractmethod
    async def traverseDown(self, obj: T) -> None:
        await self.traverseUp(obj)