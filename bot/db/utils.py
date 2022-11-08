from __future__ import annotations
from abc import ABC, abstractmethod
from typing import (TYPE_CHECKING, Generic, List,
                    Sequence, Tuple, TypeAlias, TypeVar)

import asyncpg
import discord


T = TypeVar('T')
C = TypeVar('C')
Id = int
Url = str

Record = asyncpg.Record
if TYPE_CHECKING:
    Pool: TypeAlias = asyncpg.Pool[Record]
    DBConnection: TypeAlias = asyncpg.pool.PoolConnectionProxy[Record]
else:
    Pool = asyncpg.Pool
    DBConnection = asyncpg.pool.PoolConnectionProxy



class Table:
    def __init__(self, pool: Pool) -> None:
        self.pool = pool



class Crud(Table, ABC, Generic[C]):
    def __init__(self) -> None:
        super(Table, self).__init__()

    async def insert(self, data: List[C]) -> None:
        async with self.pool.acquire() as conn:
            return await self._insert(conn, data)

    @abstractmethod
    async def _insert(self, conn: DBConnection, data: List[C]) -> None:
        raise NotImplementedError("insert not implemented for this table")


    async def update(self, data: List[C]) -> None:
        async with self.pool.acquire() as conn:
            return await self._update(conn, data)

    async def _update(self, conn: DBConnection, data: List[C]) -> None:
        return await self._insert(conn, data)

    async def soft_delete(self, data: List[Tuple[Id]]) -> None:
        async with self.pool.acquire() as conn:
            return await self._soft_delete(conn, data)

    @abstractmethod
    async def _soft_delete(self, conn: DBConnection, data: List[Tuple[Id]]) -> None:
        raise NotImplementedError(
            "soft delete not implemented for this table, perhaps try hard delete?")



class Mapper(ABC, Generic[T, C]):
    @staticmethod
    @abstractmethod
    async def prepare_one(obj: T) -> C:
        raise NotImplementedError(
            "prepare_one form object not implemented for this table")

    @staticmethod
    @abstractmethod
    async def prepare(objs: Sequence[T]) -> List[C]:
        raise NotImplementedError(
            "prepare form objects not implemented for this table")



class FromMessageMapper(ABC, Generic[C]):
    @abstractmethod
    async def prepare_from_message(self, message: discord.Message) -> List[C]:
        raise NotImplementedError(
            "prepare_from_message form objects not implemented for this table")