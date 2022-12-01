from dataclasses import dataclass, astuple
from datetime import datetime
from typing import Optional

from discord import CategoryChannel

from bot.db.utils import Crud, DBConnection, Id, Mapper, inject_conn, Entity



@dataclass
class CategoryEntity(Entity):
    __table_name__ = "server.category"

    guild_id: Id
    id: Id
    name: str
    position: int
    created_at: datetime
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None



class CategoryMapper(Mapper[CategoryChannel, CategoryEntity]):
    async def map(self, obj: CategoryChannel) -> CategoryEntity:
        category = obj
        created_at = category.created_at.replace(tzinfo=None)
        return CategoryEntity(category.guild.id, category.id, category.name, category.position, created_at)



class CategoryRepository(Crud[CategoryEntity]):
    def __init__(self) -> None:
        super().__init__(entity=CategoryEntity)


    @inject_conn
    async def insert(self, conn: DBConnection, data: CategoryEntity) -> None:
        await conn.execute(f"""
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
        """, astuple(data))
