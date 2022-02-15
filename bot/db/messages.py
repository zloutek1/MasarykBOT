import logging
from datetime import datetime
from typing import List, Optional, Tuple, cast

from asyncpg import CharacterNotInRepertoireError
from bot.db.utils import (Crud, DBConnection, Id, Mapper, Record, Table,
                          WrappedCallable, withConn)
from disnake import Message

log = logging.getLogger(__name__)

Columns = Tuple[Id, Id, Id, str, datetime]


class MessageDao(Table, Crud[Columns], Mapper[Message, Columns]):
    @staticmethod
    async def prepare_one(message: Message) -> Columns:
        created_at = message.created_at.replace(tzinfo=None)
        return (message.channel.id, message.author.id, message.id, message.content, created_at)

    async def prepare(self, messages: List[Message]) -> List[Columns]:
        return [await self.prepare_one(message) for message in messages]

    @withConn
    async def select(self, conn: DBConnection, message_id: Id) -> List[Record]:
        return await conn.fetch("""
            SELECT * FROM server.messages WHERE id=$1
        """, message_id)

    @withConn
    async def select_all_long(self, conn: DBConnection) -> List[Record]:
        return await conn.fetch("""
            SELECT * FROM server.messages
            WHERE LENGTH(content) > 50
        """)

    @withConn
    async def insert(self, conn: DBConnection, data: List[Columns]) -> None:
        try:
            await conn.executemany("""
                INSERT INTO server.messages AS m (channel_id, author_id, id, content, created_at)
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

    @withConn
    async def update(self, conn: DBConnection, data: List[Columns]) -> None:
        insert = cast(WrappedCallable, self.insert)
        await insert.__wrapped__(self, conn, data)

    @withConn
    async def soft_delete(self, conn: DBConnection, ids: List[Tuple[Id]]) -> None:
        await conn.executemany("""
            UPDATE server.messages
            SET deleted_at=NOW()
            WHERE id = $1;
        """, ids)
