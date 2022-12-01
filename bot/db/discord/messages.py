import logging
from dataclasses import dataclass, astuple
from datetime import datetime
from typing import Sequence, Tuple, Optional

from discord import Message

from bot.db.utils import (Crud, DBConnection, Id, Mapper, inject_conn, Entity, Page)

log = logging.getLogger(__name__)



@dataclass
class MessageEntity(Entity):
    channel_id: Id
    author_id: Id
    message_id: Id
    content: str
    created_at: datetime
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None



class MessageMapper(Mapper[Message, MessageEntity]):
    async def map(self, obj: Message) -> MessageEntity:
        message = obj
        created_at = message.created_at.replace(tzinfo=None)
        content = message.content.replace('\x00', '')
        return MessageEntity(message.channel.id, message.author.id, message.id, content, created_at)



class MessageRepository(Crud[MessageEntity]):
    def __init__(self) -> None:
        super().__init__(entity=MessageEntity)


    @inject_conn
    async def find_all(self, conn: DBConnection) -> Page[MessageEntity]:
        return await super().find_all(conn=conn)


    @inject_conn
    async def insert(self, conn: DBConnection, data: MessageEntity) -> None:
        await conn.execute(f"""
            INSERT INTO server.messages AS m (channel_id, author_id, id, content, created_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE
                SET content=$4,
                    created_at=$5,
                    edited_at=NOW()
                WHERE m.content<>excluded.content OR
                        m.created_at<>excluded.created_at OR
                        m.edited_at<>excluded.edited_at
        """, astuple(data))
