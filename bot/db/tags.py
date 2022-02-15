from typing import List, Optional, Tuple

from bot.db.utils import DBConnection, Id, Record, Table, withConn

Columns = Tuple[Id, Optional[Id], str, str]

class Tags(Table):
    @withConn
    async def find(
        self,
        conn: DBConnection,
        data: Tuple[Id, Optional[Id], str]
    ) -> Optional[Record]:

        guild_id, author_id, name = data
        return await conn.fetchrow("""
            SELECT * FROM cogs.tags
            WHERE guild_id = $1
              AND (author_id = $2 OR (author_id IS NULL AND $2 IS NULL))
              AND name = $3
              AND deleted_at IS NULL
        """, guild_id, author_id, name)

    @withConn
    async def findAll(
        self,
        conn: DBConnection,
        data: Tuple[Id, Optional[Id]]
    ) -> List[Record]:

        guild_id, author_id = data
        return await conn.fetch("""
            SELECT * FROM cogs.tags
            WHERE guild_id = $1
              AND (author_id = $2 OR (author_id IS NULL AND $2 IS NULL))
              AND deleted_at IS NULL
        """, guild_id, author_id)

    @withConn
    async def search(
        self,
        conn: DBConnection,
        data: Tuple[Id, Optional[Id], str]
    ) -> List[Record]:

        guild_id, author_id, query = data
        return await conn.fetch("""
            SELECT * FROM cogs.tags
            WHERE guild_id = $1
              AND (author_id = $2 OR (author_id IS NULL AND $2 IS NULL))
              AND name LIKE $3
              AND deleted_at IS NULL
        """, guild_id, author_id, query)

    @withConn
    async def insert(
        self,
        conn: DBConnection,
        data: List[Columns]
    ) -> None:

        await conn.executemany("""
            INSERT INTO cogs.tags AS t (guild_id, author_id, name, content)
                    VALUES ($1, $2, $3, $4)
            ON CONFLICT (guild_id, author_id, name) DO UPDATE
                SET content = excluded.content,
                    edited_at = NOW()
                WHERE t.content <> excluded.content;
        """, data)

    @withConn
    async def soft_delete(
        self,
        conn: DBConnection,
        data: Tuple[Id, Optional[Id], str]
    ) -> None:

        guild_id, author_id, name = data
        await conn.execute("""
            UPDATE cogs.tags
            SET deleted_at = NOW()
            WHERE guild_id = $1 AND (author_id = $2 OR $2 IS NULL) AND name = $3
        """, guild_id, author_id, name)

    @withConn
    async def copy(
        self,
        conn: DBConnection,
        data: Tuple[Id, Optional[Id], Optional[Id], str]
    ) -> None:

        guild_id, author_id, new_author_id, name = data
        await conn.execute("""
            INSERT INTO cogs.tags AS t (guild_id, author_id, name, content)
                SELECT guild_id, $3, name, content FROM cogs.tags
                WHERE guild_id = $1 AND author_id = $2 AND name = $4
            ON CONFLICT (guild_id, author_id, name) DO UPDATE
                SET content = excluded.content,
                    edited_at = NOW()
                WHERE t.content <> excluded.content;
        """, guild_id, author_id, new_author_id, name)
