from __future__ import annotations
from abc import ABC, abstractmethod
from typing import (TYPE_CHECKING, Any, Generic, List, Sequence, Tuple, TypeAlias, TypeVar)

import asyncpg


TEntity = TypeVar('TEntity')
TColumns = TypeVar('TColumns', bound=Tuple[Any, ...])
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
    def __init__(self, pool: Pool, name: str) -> None:
        self.pool = pool
        self.name = name



class Mapper(ABC, Generic[TEntity, TColumns]):    
    @staticmethod
    @abstractmethod
    async def map(obj: TEntity) -> TColumns:
        raise NotImplementedError



class Crud(Table, ABC, Generic[TColumns]):
    def __init__(self, pool: Pool, name: str) -> None:
        super(Crud, self).__init__(pool, name)


    async def find_all(self, conn: DBConnection) -> List[Record]:
        return await conn.fetch(f"""
            SELECT * FROM {self.name}
        """)


    async def find_by_id(self, conn: DBConnection, id: Id) -> Record | None:
        rows = await conn.fetch(f"""
            SELECT * FROM {self.name} WHERE id=$1
        """, id)

        if rows:
            return rows[0]
        return None


    @abstractmethod
    async def insert(self, conn: DBConnection, data: Sequence[TColumns]) -> None:
        raise NotImplementedError


    async def update(self, conn: DBConnection, data: Sequence[TColumns]) -> None:
        return await self.insert(conn, data)


    @abstractmethod
    async def soft_delete(self, conn: DBConnection, data: Sequence[Tuple[Id]]) -> None:
        raise NotImplementedError