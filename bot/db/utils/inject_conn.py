from functools import wraps
from inspect import iscoroutinefunction
from typing import Callable, Concatenate, TypeVar, ParamSpec, Coroutine, Optional

from bot.db.utils.table import Table
from bot.db.utils.types import DBConnection

S = TypeVar('S', bound=Table)
P = ParamSpec('P')
R = TypeVar('R')
Awaitable = Coroutine[None, None, R]



def inject_conn(fn: Callable[Concatenate[S, DBConnection, P], Awaitable[R]]) -> Callable[Concatenate[S, P], Awaitable[R]]:
    """
    acquire database connection from connection pool if no connection is provided

    ```py
    @inject_conn
    async def find_by_id(self, conn: DBConnection, id: int) -> Optional[Record]:
        ...
    ```

    will create a function that can be called as

    ```py
    id: int = 999
    row = await find_by_id(id)

    conn: DBConnection = ...
    row = await find_by_id(id, conn=conn)
    ```
    """
    assert iscoroutinefunction(fn), f"{fn} is not async"


    @wraps(fn)
    async def wrapper(self: S, *args: P.args, conn: Optional[DBConnection] = None, **kwargs: P.kwargs) -> R:
        if conn is not None:
            return await fn(self, conn, *args, **kwargs)
        async with self.pool.acquire() as connection:
            return await fn(self, connection, *args, **kwargs)


    return wrapper
