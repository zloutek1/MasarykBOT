import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, cast, Tuple

import discord
from discord import Message

from __oild.bot.db.utils import (Crud, DBConnection, Id, Mapper, inject_conn, Entity)

log = logging.getLogger(__name__)
BOT_PREFIXES = ('!', 'pls', '.')


@dataclass
class MessageEntity(Entity):
    __table_name__ = "server.messages"

    channel_id: Optional[Id]
    thread_id: Optional[Id]
    author_id: Id
    id: Id
    content: str
    is_command: bool
    created_at: datetime
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class MessageMapper(Mapper[Message, MessageEntity]):
    async def map(self, obj: Message) -> MessageEntity:
        message = obj
        created_at = message.created_at.replace(tzinfo=None)
        content = message.content.replace('\x00', '')
        is_command = content.startswith(BOT_PREFIXES)

        channel_id, thread_id = self.get_channel_id(message)

        return MessageEntity(channel_id, thread_id, message.author.id, message.id, content, is_command, created_at)

    @staticmethod
    def get_channel_id(message: Message) -> Tuple[Optional[Id], Optional[Id]]:
        if isinstance(message.channel, discord.abc.GuildChannel):
            return message.channel.id, None
        elif isinstance(message.channel, discord.Thread):
            return None, message.channel.id
        else:
            raise NotImplementedError(f"channel type {message.channel} not supported")


class MessageRepository(Crud[MessageEntity]):
    def __init__(self) -> None:
        super().__init__(entity=MessageEntity)

    @inject_conn
    async def insert(self, conn: DBConnection, data: MessageEntity) -> None:
        await conn.execute(f"""
            INSERT INTO server.messages AS m (channel_id, thread_id, author_id, id, content, is_command, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (id) DO UPDATE
                SET content=$5,
                    is_command=$6,
                    created_at=$7,
                    edited_at=NOW()
                WHERE m.content<>excluded.content OR
                      m.is_command<>excluded.is_command OR
                      m.created_at<>excluded.created_at OR
                      m.edited_at<>excluded.edited_at
        """, data.channel_id, data.thread_id, data.author_id, data.id, data.content, data.is_command, data.created_at)

    @inject_conn
    async def count(self, conn: DBConnection) -> int:
        row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM server.messages
        """)
        assert row, "query will always return count"
        return cast(int, row['count'])
