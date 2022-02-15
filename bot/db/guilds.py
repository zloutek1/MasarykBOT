
from datetime import datetime
from typing import List, Optional, Tuple, cast

from disnake import Guild

from .utils import (Crud, DBConnection, Id, Mapper, Record, Table, Url,
                    WrappedCallable, withConn)

Columns = Tuple[Id, str, Optional[Url], datetime]

class Guilds(Table, Crud[Columns], Mapper[Guild, Columns]):
    @staticmethod
    async def prepare_one(guild: Guild) -> Columns:
        icon_url = str(guild.icon.url) if guild.icon else None
        created_at = guild.created_at.replace(tzinfo=None)
        return (guild.id, guild.name, icon_url, created_at)

    async def prepare(self, guilds: List[Guild]) -> List[Columns]:
        return [await self.prepare_one(guild) for guild in guilds]

    @withConn
    async def select(self, conn: DBConnection, guild_id: Id) -> List[Record]:
        return await conn.fetch("""
            SELECT * FROM server.guilds WHERE id=$1
        """, guild_id)

    @withConn
    async def insert(self, conn: DBConnection, data: List[Columns]) -> None:
        await conn.executemany("""
            INSERT INTO server.guilds AS g (id, name, icon_url, created_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE
                SET name=$2,
                    icon_url=$3,
                    created_at=$4,
                    edited_at=NOW()
                WHERE g.name<>excluded.name OR
                        g.icon_url<>excluded.icon_url OR
                        g.created_at<>excluded.created_at
        """, data)

    @withConn
    async def update(self, conn: DBConnection, data: List[Columns]) -> None:
        insert = cast(WrappedCallable, self.insert)
        await insert.__wrapped__(self, conn, data)

    @withConn
    async def soft_delete(self, conn: DBConnection, ids: List[Tuple[Id]]) -> None:
        await conn.executemany("""
            UPDATE server.guilds
            SET deleted_at=NOW()
            WHERE id = $1;
        """, ids)
