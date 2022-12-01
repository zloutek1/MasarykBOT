from abc import ABC, abstractmethod
from typing import TypeVar

from .entity import Entity
from .inject_conn import inject_conn
from .page import Page
from .table import Table
from .types import DBConnection, Id

TEntity = TypeVar('TEntity', bound=Entity)



class Crud(ABC, Table[TEntity]):
    @inject_conn
    async def find_all(self, conn: DBConnection) -> Page[TEntity]:
        cursor = await conn.cursor(f"""
            SELECT *
            FROM {self.__table_name__}
        """)
        return Page(cursor, self.entity)


    @inject_conn
    async def find_by_id(self, conn: DBConnection, id: Id) -> TEntity | None:
        row = await conn.fetchrow(f"""
            SELECT * 
            FROM {self.__table_name__} 
            WHERE id=$1
        """, (id,))
        return row


    @abstractmethod
    async def insert(self, data: TEntity) -> None:
        raise NotImplementedError


    async def update(self, data: TEntity) -> None:
        return await self.insert(data)


    @inject_conn
    async def soft_delete(self, conn: DBConnection, id: Id) -> None:
        await conn.execute(f"""
            UPDATE {self.__table_name__}
            SET deleted_at=NOW()
            WHERE id = $1;
        """, (id,))
