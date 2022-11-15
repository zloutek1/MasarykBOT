from __future__ import annotations
import inject
from abc import ABC, abstractmethod
from functools import wraps
from typing import (TYPE_CHECKING, Any, Callable, Concatenate, Coroutine, 
                    Generic, List, ParamSpec, Sequence, Tuple, TypeAlias, TypeVar)

import asyncpg


TEntity = TypeVar('TEntity')
TColumns = TypeVar('TColumns', bound=Tuple[Any, ...] | Sequence[Tuple[Any, ...]])
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
    @inject.autoparams('pool')
    def __init__(self, table_name: str, pool: Pool) -> None:
        self.table_name = table_name
        self.pool = pool



class Mapper(ABC, Generic[TEntity, TColumns]):    
    @abstractmethod
    async def map(self, obj: TEntity) -> TColumns:
        raise NotImplementedError



S = TypeVar('S', bound=Table)
P = ParamSpec('P')
R = TypeVar('R')
Awaitable = Coroutine[None, None, R]



def withConn(fn: Callable[Concatenate[S, DBConnection, P], Awaitable[R]]) -> Callable[Concatenate[S, P], Awaitable[R]]:
    @wraps(fn)
    async def wrapper(self: S, *args: P.args, **kwargs: P.kwargs) -> R:
        async with self.pool.acquire() as connection:
            return await fn(self, connection, *args, **kwargs)
    return wrapper



class Crud(ABC, Generic[TColumns], Table):
    @withConn
    async def find_all(self, conn: DBConnection) -> List[Record]:
        return await conn.fetch(f"""
            SELECT * FROM {self.table_name}
        """)


    @withConn
    async def find_by_id(self, conn: DBConnection, id: Id) -> Record | None:
        rows = await conn.fetch(f"""
            SELECT * FROM {self.table_name} WHERE id=$1
        """, (id,))

        if rows:
            return rows[0]
        return None


    @abstractmethod
    async def insert(self, data: Sequence[TColumns]) -> None:
        raise NotImplementedError


    async def update(self, data: Sequence[TColumns]) -> None:
        return await self.insert(data)


    @withConn
    async def soft_delete(self, conn: DBConnection, data: Sequence[Tuple[Id]]) -> None:
        await conn.executemany(f"""
            UPDATE {self.table_name}
            SET deleted_at=NOW()
            WHERE id = $1;
        """, data)