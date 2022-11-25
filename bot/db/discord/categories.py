from datetime import datetime
from typing import Sequence, Tuple

from discord import CategoryChannel

from bot.db.tables import CATEGORIES
from bot.db.utils import (Crud, DBConnection, Id, Mapper, inject_conn)

Columns = Tuple[Id, Id, str, int, datetime]


class CategoryMapper(Mapper[CategoryChannel, Columns]):
    async def map(self, obj: CategoryChannel) -> Columns:
        category = obj
        created_at = category.created_at.replace(tzinfo=None)
        return (category.guild.id, category.id, category.name, category.position, created_at)


class CategoryRepository(Crud[Columns]):
    def __init__(self) -> None:
        super().__init__(table_name=CATEGORIES)

    @inject_conn
    async def insert(self, conn: DBConnection, data: Sequence[Columns]) -> None:
        await conn.executemany(f"""
            INSERT INTO {self.table_name} AS c (guild_id, id, name, position, created_at)
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
