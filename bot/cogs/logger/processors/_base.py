from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar('T')
R = TypeVar('R')


class Backup(ABC, Generic[T]):
    def __init__(self) -> None:
        self._backedUp: set[T] = set()

    @abstractmethod
    async def traverse_up(self, obj: T) -> None:
        if obj not in self._backedUp:
            await self.backup(obj)
            self._backedUp.add(obj)

    @abstractmethod
    async def backup(self, obj: T) -> None:
        raise NotImplementedError("Backup method is not implemented")

    @abstractmethod
    async def traverse_down(self, obj: T) -> None:
        await self.traverse_up(obj)
