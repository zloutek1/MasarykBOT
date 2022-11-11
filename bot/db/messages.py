import logging
from datetime import datetime
from typing import List, Sequence, Tuple

from discord import Message

from bot.db.utils import (Crud, DBConnection, Id, Mapper, Pool, Record, Table)
from .tables import MESSAGES



log = logging.getLogger(__name__)

Columns = Tuple[Id, Id, Id, str, datetime]



class MessageMapper(Mapper[Message, Columns]):
    @staticmethod
    async def map(obj: Message) -> Columns:
        message = obj
        created_at = message.created_at.replace(tzinfo=None)
        return (message.channel.id, message.author.id, message.id, 
                message.content, created_at)



class MessageCrudDao(Crud[Columns]):
    async def insert(self, conn: DBConnection, data: Sequence[Columns]) -> None:
        await conn.executemany(f"""
            INSERT INTO {MESSAGES} AS m (channel_id, author_id, id, content, created_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE
                SET content=$4,
                    created_at=$5,
                    edited_at=NOW()
                WHERE m.content<>excluded.content OR
                        m.created_at<>excluded.created_at OR
                        m.edited_at<>excluded.edited_at
        """, data)

    async def soft_delete(self, conn: DBConnection, data: Sequence[Tuple[Id]]) -> None:
        await conn.executemany(f"""
            UPDATE {MESSAGES}
            SET deleted_at=NOW()
            WHERE id = $1;
        """, data)



class MessageSelectDao(Table):
    def __init__(self, pool: Pool, name: str) -> None:
        super(MessageSelectDao, self).__init__(pool, name)


    async def find_all_longer_then(self, conn: DBConnection, length: int) -> List[Record]:
        return await conn.fetch(f"""
            SELECT author_id, content
            FROM {MESSAGES}
            INNER JOIN server.users AS u ON (author_id = u.id)
            WHERE LENGTH(TRIM(content)) > $1 AND 
                  NOT is_bot
        """, length)



class MessageDao(MessageCrudDao, MessageSelectDao):
    def __init__(self, pool: Pool, name: str) -> None:
        super().__init__(pool, name)