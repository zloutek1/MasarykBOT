from collections.abc import AsyncIterator
from typing import TypeVar, List

from .entity import Entity
from .types import Cursor


TEntity = TypeVar('TEntity', bound=Entity)


class Page(AsyncIterator[List[TEntity]]):
    def __init__(self, cursor: Cursor, entity: TEntity, per_page: int = 50) -> None:
        self.cursor = cursor
        self.entity = entity
        self.per_page = per_page

    def __aiter__(self) -> "Page[TEntity]":
        return self

    async def __anext__(self) -> List[TEntity]:
        if not (rows := await self.cursor.fetch(self.per_page)):
            raise StopAsyncIteration
        return [self.entity.convert(row) for row in rows]

    