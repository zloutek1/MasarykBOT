from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from discord import TextChannel

from bot.db.utils import Crud, DBConnection, Id, Mapper, inject_conn, Entity



@dataclass
class ChannelEntity(Entity):
    __table_name__ = "server.channel"

    guild_id: Id
    category_id: Optional[Id]
    id: Id
    name: str
    position: int
    created_at: datetime
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None



class ChannelMapper(Mapper[TextChannel, ChannelEntity]):
    async def map(self, obj: TextChannel) -> ChannelEntity:
        channel = obj
        category_id = channel.category.id if channel.category is not None else None
        created_at = channel.created_at.replace(tzinfo=None)
        return ChannelEntity(channel.guild.id, category_id, channel.id, channel.name, channel.position, created_at)



class ChannelRepository(Crud[ChannelEntity]):
    def __init__(self) -> None:
        super().__init__(entity=ChannelEntity)


    @inject_conn
    async def insert(self, conn: DBConnection, data: ChannelEntity) -> None:
        await conn.execute(f"""
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
        """, data.guild_id, data.category_id, data.id, data.name, data.position, data.created_at)
