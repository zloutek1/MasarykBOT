import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from discord import Message

from bot.db.utils import (Crud, DBConnection, Id, Mapper, inject_conn, Entity)

log = logging.getLogger(__name__)
BOT_PREFIXES = ('!', 'pls', '.')


@dataclass
class MessageEntity(Entity):
    __table_name__ = "server.messages"

    channel_id: Id
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

        return MessageEntity(message.channel.id, message.author.id, message.id, content, is_command, created_at)



class MessageRepository(Crud[MessageEntity]):
    def __init__(self) -> None:
        super().__init__(entity=MessageEntity)


    @inject_conn
    async def insert(self, conn: DBConnection, data: MessageEntity) -> None:
        await conn.execute(f"""
            INSERT INTO server.messages AS m (channel_id, author_id, id, content, is_command, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO UPDATE
                SET content=$4,
                    is_command=$5,
                    created_at=$6,
                    edited_at=NOW()
                WHERE m.content<>excluded.content OR
                      m.is_command<>excluded.is_command OR
                      m.created_at<>excluded.created_at OR
                      m.edited_at<>excluded.edited_at
        """, data.channel_id, data.author_id, data.id, data.content, data.is_command, data.created_at)


    @inject_conn
    async def count(self, conn: DBConnection) -> int:
        row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM server.messages
        """)
        return row['count']
