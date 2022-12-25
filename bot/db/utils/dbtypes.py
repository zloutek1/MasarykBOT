from typing import TYPE_CHECKING, TypeAlias

import asyncpg.cursor
import asyncpg.transaction

Id = int

Url = str

Record = asyncpg.Record

DBTransaction = asyncpg.transaction.Transaction

if TYPE_CHECKING:
    Cursor = asyncpg.cursor.Cursor[Record]
else:
    Cursor = asyncpg.cursor.Cursor

if TYPE_CHECKING:
    Pool: TypeAlias = asyncpg.Pool[asyncpg.Record] # type: ignore
else:
    Pool = asyncpg.Pool

if TYPE_CHECKING:
    DBConnection = asyncpg.pool.PoolConnectionProxy[Record]
else:
    DBConnection = asyncpg.pool.PoolConnectionProxy
