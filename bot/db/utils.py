from abc import ABC, abstractmethod
from functools import wraps
from inspect import signature
from typing import (Any, Awaitable, Callable, Coroutine, Generic, List,
                    Optional, Tuple, TypeVar, Union, cast, overload)

import asyncpg
import disnake as discord

T = TypeVar('T')
R = TypeVar('R')
C = TypeVar('C')
Id = int
Url = str
Pool = asyncpg.Pool
Record = asyncpg.Record
DBConnection = asyncpg.pool.PoolConnectionProxy[Record]


class WrappedCallable(Generic[R]):
    """Stub for a Callable with a __wrapped__ attribute."""

    __wrapped__: Callable[..., R]
    __name__: str

    def __call__(self, *args: Any, **kwargs: Any) -> R:
        ...


class Table:
    def __init__(self, pool: Pool):
        self.pool = pool


class Crud(ABC, Generic[C]):
    @abstractmethod
    async def insert(self, data: List[C]) -> None:
        raise NotImplementedError("insert not implemented for this table")

    @abstractmethod
    async def update(self, data: List[C]) -> None:
        raise NotImplementedError("update not implemented for this table")

    async def delete(self, data: List[Tuple[Id]]) -> None:
        raise NotImplementedError(
            "hard delete not implemented for this table, perhaps try soft delete?")

    @abstractmethod
    async def soft_delete(self, data: List[Tuple[Id]]) -> None:
        raise NotImplementedError(
            "soft delete not implemented for this table, perhaps try hard delete?")


class Mapper(ABC, Generic[T, C]):
    @staticmethod
    @abstractmethod
    async def prepare_one(obj: T) -> C:
        raise NotImplementedError(
            "prepare_one form object not implemented for this table")

    @abstractmethod
    async def prepare(self, objs: List[T]) -> List[C]:
        raise NotImplementedError(
            "prepare form objects not implemented for this table")


class FromMessageMapper(ABC, Generic[C]):
    @abstractmethod
    async def prepare_from_message(self, message: discord.Message) -> List[C]:
        raise NotImplementedError(
            "prepare_from_message form objects not implemented for this table")


S = TypeVar('S', bound=Table)

@overload
def withConn(
    func: Callable[[S, DBConnection], Awaitable[R]]
) -> Callable[[S], Coroutine[Any, Any, R]]:
    ...

@overload
def withConn(
    func: Callable[[S, DBConnection, T], Awaitable[R]]
) -> Callable[[S, T], Coroutine[Any, Any, R]]:
    ...

def withConn(
    func: Union[
        Callable[[S, DBConnection], Awaitable[R]],
        Callable[[S, DBConnection, T], Awaitable[R]]
    ]
) -> Union[
    Callable[[S], Coroutine[Any, Any, R]],
    Callable[[S, T], Coroutine[Any, Any, R]]
]:
    """
    This function is a decorator
    that acquires and injects a database connection
    into a function

    Ex.
    ```py
    @withConn
    async def select(self, conn: DBConnection, data: Tuple[Id]) -> List[Record]:
        ...
    ```

    The example above will abstract the connection from the user and
    transform the select function into

    ```py
    async def select(self, data: Tuple[Id]) -> List[Record]:
        ...
    ```

    The original function can still be accesses using

    ```py
    w_select = cast(WrappedCallable, select)
    w_select.__warpped__(conn, data)
    ```

    """

    @wraps(func)
    async def wrapper_one_arg(self: S, data: T) -> R:
        func = cast(Callable[[S, DBConnection, T], Awaitable[R]], func)
        async with self.pool.acquire() as conn:
            return await func(self, conn, data)

    @wraps(func)
    async def wrapper_no_args(self: S) -> R:
        func = cast(Callable[[S, DBConnection], Awaitable[R]], func)
        async with self.pool.acquire() as conn:
            return await func(self, conn)

    argc = len(signature(func).parameters)
    if argc == 2:
        return wrapper_no_args
    elif argc == 3:
        return wrapper_one_arg
    else:
        raise NotImplementedError

