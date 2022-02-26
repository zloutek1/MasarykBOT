from datetime import date, datetime
from typing import List, Optional, Tuple, cast

from bot.db.utils import (Crud, DBConnection, Id, Record, Table,
                          WrappedCallable, withConn)

Columns = Tuple[Id, str, Optional[datetime], Optional[datetime], Optional[bytes], Optional[bytes]]

class SeasonDao(Table, Crud[Columns]):
    @withConn
    async def load_events(self, conn: DBConnection, guild_id: Id) -> List[Record]:

        return await conn.fetch("""
            SELECT * FROM cogs.seasons
            WHERE guild_id = $1 AND
                  from_date IS NOT NULL AND
                  to_date IS NOT NULL
            ORDER BY to_date ASC, from_date DESC
        """, guild_id)

    @withConn
    async def find(self, conn: DBConnection, data: Tuple[Id, Id]) -> Optional[Record]:

        guild_id, id = data
        return await conn.fetchrow("""
            SELECT * FROM cogs.seasons
            WHERE guild_id = $1 AND
                  id = $2 AND
                  from_date IS NOT NULL AND
                  to_date IS NOT NULL
            ORDER BY to_date ASC, from_date DESC
        """, guild_id, id)

    @withConn
    async def load_current_event(self, conn: DBConnection, guild_id: Id) -> Optional[Record]:

        return await conn.fetchrow("""
            SELECT * FROM cogs.seasons
            WHERE guild_id = $1 AND
                  from_date < NOW() AND
                  NOW() < to_date
		 	ORDER BY (to_date - from_date)
        """, guild_id)

    @withConn
    async def load_default_event(self, conn: DBConnection, guild_id: Id) -> Optional[Record]:
        return await conn.fetchrow("""
            SELECT * FROM cogs.seasons
            WHERE guild_id = $1 AND
                  name = 'default'
        """, guild_id)

    @withConn
    async def insert(self, conn: DBConnection, data: List[Columns]) -> None:
        await conn.executemany("""
            INSERT INTO cogs.seasons AS s (guild_id, name, from_date, to_date, icon, banner)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (guild_id, name) DO UPDATE
                SET icon = excluded.icon,
                    banner = excluded.banner
        """, data)

    @withConn
    async def update(self, conn: DBConnection, data: List[Columns]) -> None:
        insert = cast(WrappedCallable, self.insert)
        await insert.__wrapped__(self, conn, data)

    # TODO: rework the seasons cog to use soft deletes
    @withConn
    async def delete(self, conn: DBConnection, data: List[Tuple[Id]]) -> None:
        await conn.executemany("""
            DELETE FROM cogs.seasons
            WHERE id = $1
        """, data)

    @withConn
    async def soft_delete(self, conn: DBConnection, data: List[Tuple[Id]]) -> None:
        await self.delete(data)
