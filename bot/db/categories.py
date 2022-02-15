from datetime import datetime
from typing import List, Tuple, cast

from bot.db.utils import (Crud, DBConnection, Id, Mapper, Record, Table,
                          WrappedCallable, withConn)
from disnake import CategoryChannel

Columns = Tuple[Id, Id, str, int, datetime]

class CategoryDao(Table, Crud[Columns], Mapper[CategoryChannel, Columns]):
    @staticmethod
    async def prepare_one(category: CategoryChannel) -> Columns:
        created_at = category.created_at.replace(tzinfo=None)
        return (category.guild.id, category.id, category.name, category.position, created_at)

    async def prepare(self, categories: List[CategoryChannel]) -> List[Columns]:
        return [await self.prepare_one(category) for category in categories]

    @withConn
    async def select(self, conn: DBConnection, category_id: Id) -> List[Record]:
        return await conn.fetch("""
            SELECT * FROM server.categories WHERE id=$1
        """, category_id)

    @withConn
    async def insert(self, conn: DBConnection, data: List[Columns]) -> None:
        await conn.executemany("""
            INSERT INTO server.categories AS c (guild_id, id, name, position, created_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE
                SET name=$3,
                    position=$4,
                    created_at=$5,
                    edited_at=NOW()
                WHERE c.name<>excluded.name OR
                        c.position<>excluded.position OR
                        c.created_at<>excluded.created_at
        """, data)

    @withConn
    async def update(self, conn: DBConnection, data: List[Columns]) -> None:
        insert = cast(WrappedCallable, self.insert)
        await insert.__wrapped__(self, conn, data)

    @withConn
    async def soft_delete(self, conn: DBConnection, ids: List[Tuple[Id]]) -> None:
        await conn.executemany("""
            UPDATE server.categories
            SET deleted_at=NOW()
            WHERE id = $1;
        """, ids)
