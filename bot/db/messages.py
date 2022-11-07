import logging
from datetime import datetime
from typing import List, Sequence, Tuple

from asyncpg import CharacterNotInRepertoireError
from bot.db.utils import (Crud, DBConnection, Id, Mapper, Record, Table)
from discord import Message
from .tables import MESSAGES

log = logging.getLogger(__name__)

Columns = Tuple[Id, Id, Id, str, datetime]



class MessageMapper(Mapper[Message, Columns]):
    @staticmethod
    async def prepare_one(obj: Message) -> Columns:
        message = obj
        created_at = message.created_at.replace(tzinfo=None)
        return (message.channel.id, message.author.id, message.id, 
                message.content, created_at)

    @staticmethod
    async def prepare(objs: Sequence[Message]) -> List[Columns]:
        messages = objs
        return [await MessageMapper.prepare_one(message) for message in messages]



class MessageCrudDao(Crud[Columns]):
    async def _insert(self, conn: DBConnection, data: List[Columns]) -> None:
        try:
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
        except CharacterNotInRepertoireError as e:
            log.warn(e.message)

    async def _soft_delete(self, conn: DBConnection, data: List[Tuple[Id]]) -> None:
        await conn.executemany(f"""
            UPDATE {MESSAGES}
            SET deleted_at=NOW()
            WHERE id = $1;
        """, data)



class MessageSelectDao(Table):
    def __init__(self) -> None:
        super(Table, self).__init__()

    async def select(self, message_id: Id) -> List[Record]:
        async with self.pool.acquire() as conn:
            return await self._select(conn, message_id)

    async def _select(self, conn: DBConnection, message_id: Id) -> List[Record]:
        return await conn.fetch(f"""
            SELECT * FROM {MESSAGES} WHERE id=$1
        """, message_id)


    async def select_longer_then(self, length: int) -> List[Record]:
        async with self.pool.acquire() as conn:
            return await self._select_longer_then(conn, length)

    async def _select_longer_then(self, conn: DBConnection, length: int) -> List[Record]:
        return await conn.fetch(f"""
            SELECT author_id, content
            FROM {MESSAGES}
            INNER JOIN server.users AS u ON (author_id = u.id)
            WHERE LENGTH(TRIM(content)) > $1 AND 
                  NOT is_bot
        """, length)



class MessageDao(MessageMapper, MessageCrudDao, MessageSelectDao):
    def __init__(self) -> None:
        super(MessageMapper, self).__init__()
        super(MessageCrudDao, self).__init__()
        super(MessageSelectDao, self).__init__()