from datetime import datetime
from typing import List, Optional, Tuple, cast

from bot.db.utils import (Crud, DBConnection, Id, Mapper, Record, Table,
                          WrappedCallable, withConn)
from disnake import TextChannel

Columns = Tuple[Id, Optional[Id], Id, str, int, datetime]

class ChannelDao(Table, Crud[Columns], Mapper[TextChannel, Columns]):
    @staticmethod
    async def prepare_one(channel: TextChannel) -> Columns:
        category_id = channel.category.id if channel.category is not None else None
        created_at = channel.created_at.replace(tzinfo=None)
        return (channel.guild.id, category_id, channel.id, channel.name, channel.position, created_at)

    async def prepare(self, channels: List[TextChannel]) -> List[Columns]:
        return [await self.prepare_one(channel) for channel in channels]

    @withConn
    async def select(self, conn: DBConnection, channel_id: Id) -> List[Record]:
        return await conn.fetch("""
            SELECT * FROM server.channels WHERE id=$1
        """, channel_id)

    @withConn
    async def insert(self, conn: DBConnection, data: List[Columns]) -> None:
        await conn.executemany("""
            INSERT INTO server.channels AS ch (guild_id, category_id, id, name, position, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO UPDATE
                SET name=$4,
                    position=$5,
                    created_at=$6,
                    edited_at=NOW()
                WHERE ch.name<>excluded.name OR
                        ch.position<>excluded.position OR
                        ch.created_at<>excluded.created_at
        """, data)

    @withConn
    async def update(self, conn: DBConnection, data: List[Columns]) -> None:
        insert = cast(WrappedCallable, self.insert)
        await insert.__wrapped__(self, conn, data)

    @withConn
    async def soft_delete(self, conn: DBConnection, ids: List[Tuple[Id]]) -> None:
        await conn.executemany("""
            UPDATE server.channels
            SET deleted_at=NOW()
            WHERE id = $1;
        """, ids)
