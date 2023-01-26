from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from bot.db.utils import inject_conn, DBConnection, Entity, Crud


@dataclass
class FacultyEntity(Entity):
    __table_name__ = "muni.faculties"

    id: int
    code: str
    name: str
    created_at: datetime
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class FacultyRepository(Crud[FacultyEntity]):
    def __init__(self) -> None:
        super().__init__(entity=FacultyEntity)

    @inject_conn
    async def insert(self, conn: DBConnection, data: FacultyEntity) -> None:
        print(data)
        await conn.execute("""
            INSERT INTO muni.faculties (id, code, name)
            VALUES ($1, $2, $3)
            ON CONFLICT (id) DO UPDATE
                SET code=$2,
                    name=$3
        """, data.id, data.code, data.name)

    @inject_conn
    async def soft_delete(self, conn: DBConnection, data: FacultyEntity) -> None:
        await conn.execute("""
            UPDATE muni.faculties
            SET deleted_at=NOW()
            WHERE id=$1 AND code=$2 AND name=$3
        """, data.id, data.code, data.name)
