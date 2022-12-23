from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Iterable, cast

from bot.db.utils import inject_conn, DBConnection, Url, Entity, Table



@dataclass
class CourseEntity(Entity):
    __table_name__ = "muni.courses"

    faculty: str
    code: str
    name: str
    url: Url
    terms: List[str]
    created_at: datetime
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None



class CourseRepository(Table[CourseEntity]):
    def __init__(self) -> None:
        super().__init__(entity=CourseEntity)


    @inject_conn
    async def autocomplete(self, conn: DBConnection, pattern: str) -> List[CourseEntity]:
        rows = await conn.fetch(f"""
            SELECT *
            FROM muni.courses
            WHERE lower(faculty||':'||code||' '||substr(name, 1, 50)) LIKE lower($1)
            LIMIT 25
        """, pattern)
        return CourseEntity.convert_many(rows)


    @inject_conn
    async def find_by_code(self, conn: DBConnection, faculty: str, code: str) -> Optional[CourseEntity]:
        row = await conn.fetchrow(f"""
            SELECT *
            FROM muni.courses
            WHERE lower(faculty)=lower($1) AND lower(code)=lower($2)
        """, faculty, code)
        return CourseEntity.convert(row) if row else None


    @inject_conn
    async def find_all_courses(self, conn: DBConnection) -> Iterable[str]:
        rows = await conn.fetch(f"""
            SELECT faculty||':'||code as result
            FROM muni.courses
        """)
        return map(lambda row: cast(str, row['result']), rows)


    @inject_conn
    async def find_courses(self, conn: DBConnection, data: List[str]) -> Iterable[CourseEntity]:
        rows = await conn.fetch(f"""
                SELECT *
                FROM muni.courses
                WHERE (faculty||':'||code)=ANY($1::varchar[])
            """, data)
        return CourseEntity.convert_many(rows)
