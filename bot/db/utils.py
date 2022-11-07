from abc import ABC, abstractmethod
from typing import (Generic, List,
                    Sequence, Tuple, TypeVar)

import asyncpg
import discord
import inject



T = TypeVar('T')
C = TypeVar('C')
Id = int
Url = str
Record = asyncpg.Record
Pool = asyncpg.Pool[Record]
DBConnection = asyncpg.pool.PoolConnectionProxy[Record]


class Table:
    pool = inject.attr(Pool)

    def __init__(self):
        if self.pool is None:
            raise Exception("database connection is required")



class Crud(Table, ABC, Generic[C]):
    def __init__(self):
        super(Table).__init__()

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