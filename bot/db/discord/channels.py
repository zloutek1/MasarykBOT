import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import discord
from discord.abc import GuildChannel

from bot.db.utils import Crud, DBConnection, Id, Mapper, inject_conn, Entity



class ChannelType(enum.Enum):
    TEXT = "text"
    FORUM = "forum"


@dataclass
class ChannelEntity(Entity):
    __table_name__ = "server.channel"

    guild_id: Id
    category_id: Optional[Id]
    id: Id
    name: str
    type: ChannelType
    created_at: datetime
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None



class ChannelMapper(Mapper[GuildChannel, ChannelEntity]):
    async def map(self, obj: GuildChannel) -> ChannelEntity:
        channel = obj
        channel_type = self.get_channel_type(channel)
        category_id = channel.category.id if channel.category is not None else None
        created_at = channel.created_at.replace(tzinfo=None)
        return ChannelEntity(channel.guild.id, category_id, channel.id, channel.name, channel_type, created_at)

    @staticmethod
    def can_map(channel: GuildChannel) -> bool:
        return channel.type in [discord.ChannelType.text, discord.ChannelType.forum]

    @staticmethod
    def get_channel_type(channel: GuildChannel) -> ChannelType:
        match channel.type:
            case discord.ChannelType.text: return ChannelType.TEXT
            case discord.ChannelType.forum: return ChannelType.FORUM
        raise NotImplementedError(f"unsupported channel type {channel.type}")



class ChannelRepository(Crud[ChannelEntity]):
    def __init__(self) -> None:
        super().__init__(entity=ChannelEntity)


    @inject_conn
    async def insert(self, conn: DBConnection, data: ChannelEntity) -> None:
        await conn.execute(f"""
            INSERT INTO server.channels AS ch (guild_id, category_id, id, "name", "type", created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO UPDATE
                SET name=$4,
                    created_at=$6,
                    edited_at=NOW()
                WHERE ch.name<>excluded.name OR
                      ch.created_at<>excluded.created_at
        """, data.guild_id, data.category_id, data.id, data.name, data.type.value, data.created_at)
