from typing import Tuple, Optional

from bot.db.tables import STUDENTS
from bot.db.utils import inject_conn, DBConnection, Id, Crud

Columns = Tuple[str, str, Id, Id]


class StudentRepository(Crud[Columns]):
    def __init__(self):
        super().__init__(table_name=STUDENTS)


    @inject_conn
    async def insert(self, conn: DBConnection, data: Tuple[Columns]) -> None:
        await conn.execute("""
            INSERT INTO muni.students (faculty, code, guild_id, member_id)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (faculty, code, guild_id, member_id) DO UPDATE 
                SET left_at=NULL
        """, *data)


    @inject_conn
    async def count_course_students(self, conn: DBConnection, data: Tuple[str, str, Id]) -> Optional[int]:
        row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM muni.students
            WHERE faculty=$1 AND code=$2 AND guild_id=$3 AND left_at IS NULL
        """, *data)
        return row['count'] if row else None


    @inject_conn
    async def soft_delete(self, conn: DBConnection, data: Tuple[str, str, Id, Id]) -> None:
        await conn.execute("""
            UPDATE muni.students
            SET left_at=NOW()
            WHERE faculty=$1 AND code=$2 AND guild_id=$3 AND member_id=$4
        """, *data)
