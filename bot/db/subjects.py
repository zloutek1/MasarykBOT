
from datetime import datetime
from typing import List, Optional, Tuple

from .utils import DBConnection, Id, Record, Table, withConn
from .tables import SUBJECTS, REGISTERS, SUBJECT_SERVER, SUBJECT_CATEGORY

def get_term(date: datetime):
    return f"jaro {date.year}" if 3 <= date.month < 9 else f"podzim {date.year}"

class SubjectDao(Table):
    @withConn
    async def find(self, conn: DBConnection, data: Tuple[str, str]) -> List[Record]:
        faculty, code = data
        return await conn.fetch(f"""
            SELECT *
            FROM {SUBJECTS}
            WHERE LOWER(faculty) = LOWER($1) AND
                  LOWER(code) LIKE LOWER($2)
        """, faculty, code)

    @withConn
    async def find_all_recent_for_faculty(self, conn: DBConnection, data: Tuple[str, datetime]) -> List[Record]:
        faculty, date = data
        return await conn.fetch(f"""
            SELECT faculty, code, name
            FROM {SUBJECTS}
            WHERE LOWER(faculty) = LOWER($1) AND
                  $2 = ANY(terms)
        """, faculty, get_term(date))

    @withConn
    async def find_registered(
        self,
        conn: DBConnection,
        data: Tuple[Id, str, str]
    ) -> Optional[Record]:

        guild_id, faculty, code = data
        return await conn.fetchrow(f"""
            SELECT *
            FROM {REGISTERS}
            WHERE guild_id = $1 AND
                  LOWER(faculty) = LOWER($2) AND
                  LOWER(code) LIKE LOWER($3)
        """, guild_id, faculty, code)

    @withConn
    async def find_serverinfo(
        self,
        conn: DBConnection,
        data: Tuple[Id, str, str]
    ) -> Optional[Record]:

        guild_id, faculty, code = data
        return await conn.fetchrow(f"""
            SELECT *
            FROM {SUBJECT_SERVER}
            WHERE guild_id = $1 AND
                  LOWER(faculty) = LOWER($2) AND
                  LOWER(code) LIKE LOWER($3)
        """, guild_id, faculty, code)

    @withConn
    async def find_users_subjects(
        self,
        conn: DBConnection,
        data: Tuple[Id, Id]
    ) -> List[Record]:

        guild_id, member_id = data
        return await conn.fetch(f"""
            SELECT *
            FROM {REGISTERS}
            WHERE guild_id = $1 AND
                  $2::bigint = ANY(member_ids)
        """, guild_id, member_id)

    @withConn
    async def sign_user(
        self,
        conn: DBConnection,
        data: Tuple[Id, str, str, Id]
    ) -> None:

        guild_id, faculty, code, member_id = data
        await conn.execute(f"""
            INSERT INTO {REGISTERS} AS r (guild_id, faculty, code, member_ids)
                   VALUES ($1, $2, $3, ARRAY[$4::bigint])
            ON CONFLICT (guild_id, code) DO UPDATE
                SET member_ids = array_append(r.member_ids, $4::bigint)
                WHERE $4::bigint <> ALL(r.member_ids);
        """, guild_id, faculty, code, member_id)

    @withConn
    async def unsign_user(
        self,
        conn: DBConnection,
        data: Tuple[Id, str, str, Id]
    ) -> None:

        guild_id, faculty, code, member_id = data
        await conn.execute(f"""
            UPDATE {REGISTERS}
                SET member_ids = array_remove(member_ids, $4::bigint)
                WHERE guild_id = $1 AND
                      LOWER(faculty) = LOWER($2) AND
                      LOWER(code) = LOWER($3) AND
                      $4 = ANY(member_ids);
        """, guild_id, faculty, code, member_id)

    @withConn
    async def unsign_user_from_all(
        self,
        conn: DBConnection,
        data: Tuple[Id, Id]
    ) -> None:

        guild_id, member_id = data
        await conn.execute(f"""
            UPDATE {REGISTERS}
                SET member_ids = array_remove(member_ids, $2::bigint)
                WHERE guild_id = $1 AND
                      $2::bigint = ANY(member_ids)
        """, guild_id, member_id)


    @withConn
    async def get_category(
        self,
        conn: DBConnection,
        data: Tuple[Id, str, str]
    ) -> Optional[Record]:

        guild_id, faculty, code = data
        return await conn.fetchrow(f"""
            SELECT *
            FROM {SUBJECT_CATEGORY}
            WHERE guild_id = $1 AND
                  LOWER(faculty) = LOWER($2) AND
                  LOWER(code) LIKE LOWER($3)
        """, guild_id, faculty, code)

    @withConn
    async def set_category(
        self,
        conn: DBConnection,
        data: Tuple[Id, str, str, Id]
    ) -> None:

        guild_id, faculty, code, category_id = data
        await conn.execute(f"""
            UPDATE {SUBJECT_SERVER}
                SET category_id = $4
                WHERE guild_id = $1 AND
                      LOWER(faculty) = LOWER($2) AND
                      LOWER(code) LIKE LOWER($3);
        """, guild_id, faculty, code, category_id)

    @withConn
    async def set_channel(
        self,
        conn: DBConnection, data: Tuple[Id, str, str, Id]
    ) -> None:

        guild_id, faculty, code, channel_id = data
        await conn.execute(f"""
            INSERT INTO {SUBJECT_SERVER} AS ss (guild_id, faculty, code, channel_id)
                    VALUES ($1, $2, $3, $4)
            ON CONFLICT (guild_id, faculty, code) DO UPDATE
                SET channel_id = excluded.channel_id
                WHERE ss.channel_id IS NULL OR ss.channel_id <> excluded.channel_id;
        """, guild_id, faculty, code, channel_id)

    @withConn
    async def remove_channel(
        self,
        conn: DBConnection,
        data: Tuple[Id, str, str]
    ) -> None:

        guild_id, faculty, code = data
        await conn.execute(f"""
            DELETE FROM {SUBJECT_SERVER}
                WHERE guild_id = $1 AND
                      LOWER(faculty) = LOWER($2) AND
                      LOWER(code) = LOWER($3)
        """, guild_id, faculty, code)

