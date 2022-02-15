
from typing import List, Optional, Tuple

from .utils import DBConnection, Id, Record, Table, withConn


class Subjects(Table):
    @withConn
    async def find(self, conn: DBConnection, data: Tuple[str, str]) -> List[Record]:
        faculty, code = data
        return await conn.fetch("""
            SELECT *
            FROM muni.subjects
            WHERE LOWER(faculty) = LOWER($1) AND
                  LOWER(code) LIKE LOWER($2)
        """, faculty, code)

    @withConn
    async def find_registered(
        self,
        conn: DBConnection,
        data: Tuple[Id, str, str]
    ) -> Optional[Record]:

        guild_id, faculty, code = data
        return await conn.fetchrow("""
            SELECT *
            FROM muni.registers
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
        return await conn.fetchrow("""
            SELECT *
            FROM muni.subject_server
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
        return await conn.fetch("""
            SELECT *
            FROM muni.registers
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
        await conn.execute("""
            INSERT INTO muni.registers AS r (guild_id, faculty, code, member_ids)
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
        await conn.execute("""
            UPDATE muni.registers
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
        await conn.execute("""
            UPDATE muni.registers
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
        return await conn.fetchrow("""
            SELECT *
            FROM muni.subject_category
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
        await conn.execute("""
            UPDATE muni.subject_server
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
        await conn.execute("""
            INSERT INTO muni.subject_server AS ss (guild_id, faculty, code, channel_id)
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
        await conn.execute("""
            DELETE FROM muni.subject_server
                WHERE guild_id = $1 AND
                      LOWER(faculty) = LOWER($2) AND
                      LOWER(code) = LOWER($3)
        """, guild_id, faculty, code)

