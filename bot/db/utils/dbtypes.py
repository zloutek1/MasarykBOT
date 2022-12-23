from typing import TYPE_CHECKING

import asyncpg.cursor
import asyncpg.pool
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
    Pool = asyncpg.pool.Pool[Record] # ignore: misc
else:
    Pool = asyncpg.pool.Pool

if TYPE_CHECKING:
    DBConnection = asyncpg.pool.PoolConnectionProxy[Record]
else:
    DBConnection = asyncpg.pool.PoolConnectionProxy
