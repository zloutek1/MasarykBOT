from datetime import datetime
from typing import Optional, Sequence, Tuple

from discord import TextChannel

from bot.db.tables import CHANNELS
from bot.db.utils import (Crud, DBConnection, Id, Mapper, withConn)



Columns = Tuple[Id, Optional[Id], Id, str, int, datetime]



class ChannelMapper(Mapper[TextChannel, Columns]):
    async def map(self, obj: TextChannel) -> Columns:
        channel = obj
        category_id = channel.category.id if channel.category is not None else None
        created_at = channel.created_at.replace(tzinfo=None)
        return (channel.guild.id, category_id, channel.id, channel.name, channel.position, created_at)



class ChannelDao(Crud[Columns]):
    def __init__(self) -> None:
        super().__init__(table_name=CHANNELS)


    @withConn
    async def insert(self, conn: DBConnection, data: Sequence[Columns]) -> None:
        await conn.executemany(f"""
            INSERT INTO {CHANNELS} AS ch (guild_id, category_id, id, name, position, created_at)
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