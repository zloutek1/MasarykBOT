from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from collections import deque

T = TypeVar('T')
R = TypeVar('R')


class Backup(ABC, Generic[T]):
    def __init__(self) -> None:
        self._backedUp: deque[T] = deque(maxlen=200)

    @abstractmethod
    async def traverse_up(self, obj: T) -> None:
        if obj not in self._backedUp:
            self._backedUp.append(obj)
            await self.backup(obj)

    @abstractmethod
    async def backup(self, obj: T) -> None:
        raise NotImplementedError("Backup method is not implemented")

    @abstractmethod
    async def traverse_down(self, obj: T) -> None:
        await self.traverse_up(obj)
