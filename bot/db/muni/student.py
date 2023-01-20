from dataclasses import dataclass, astuple
from typing import Tuple, Optional, Iterable, cast

from bot.db.utils import inject_conn, DBConnection, Id, Crud, Entity


@dataclass
class StudentEntity(Entity):
    __table_name__ = "muni.students"

    faculty: str
    code: str
    guild_id: Id
    member_id: Id


class StudentRepository(Crud[StudentEntity]):
    def __init__(self) -> None:
        super().__init__(entity=StudentEntity)

    @inject_conn
    async def insert(self, conn: DBConnection, data: StudentEntity) -> None:
        await conn.execute("""
            INSERT INTO muni.students (faculty, code, guild_id, member_id)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (faculty, code, guild_id, member_id) DO UPDATE 
                SET left_at=NULL
        """, astuple(data))

    @inject_conn
    async def count_course_students(self, conn: DBConnection, data: Tuple[str, str, Id]) -> int:
        row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM muni.students
            WHERE faculty=$1 AND code=$2 AND guild_id=$3 AND left_at IS NULL
        """, *data)
        assert row
        return cast(int, row['count'])

    @inject_conn
    async def find_all_students_courses(self, conn: DBConnection, data: Tuple[Id, Id]) -> Iterable[str]:
        rows = await conn.fetch("""
                SELECT faculty||':'||code as result
                FROM muni.students
                WHERE guild_id=$1 AND member_id=$2 AND left_at IS NULL
            """, *data)
        return map(lambda row: cast(str, row['result']), rows)

    @inject_conn
    async def soft_delete(self, conn: DBConnection, data: StudentEntity) -> None:
        await conn.execute("""
            UPDATE muni.students
            SET left_at=NOW()
            WHERE faculty=$1 AND code=$2 AND guild_id=$3 AND member_id=$4
        """, astuple(data))
