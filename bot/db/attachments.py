from datetime import datetime
from typing import List, Optional, Sequence, Tuple, cast

from bot.db.tables import ATTACHMENTS
from bot.db.utils import (Crud, DBConnection, FromMessageMapper, Id, Mapper,
                          Record, Table, Url, WrappedCallable, withConn)
from disnake import Attachment, Message

Columns = Tuple[Optional[Id], Id, str, Url]

class AttachmentDao(Table, Crud[Columns], Mapper[Attachment, Columns], FromMessageMapper[Columns]):
    @staticmethod
    async def prepare_one(attachment: Attachment) -> Columns:
        return (None, attachment.id, attachment.filename, attachment.url)

    async def prepare(self, attachments: Sequence[Attachment]) -> List[Columns]:
        return [await self.prepare_one(attachment) for attachment in attachments]

    async def prepare_from_message(self, message: Message) -> List[Columns]:
        return [(message.id, attachment_id, filename, url)
                for (_, attachment_id, filename, url) in await self.prepare(message.attachments)
               ]

    @withConn
    async def select(self, conn: DBConnection, attachment_id: Id) -> List[Record]:
        return await conn.fetch(f"""
            SELECT * FROM {ATTACHMENTS} WHERE id=$1
        """, attachment_id)

    @withConn
    async def insert(self, conn: DBConnection, data: List[Columns]) -> None:
        await conn.executemany(f"""
            INSERT INTO {ATTACHMENTS} AS a (message_id, id, filename, url)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE
                SET filename=$3,
                    url=$4
                WHERE a.filename<>excluded.filename OR
                        a.url<>excluded.url
        """, data)

    @withConn
    async def update(self, conn: DBConnection, data: List[Columns]) -> None:
        insert = cast(WrappedCallable, self.insert)
        await insert.__wrapped__(self, conn, data)

    # TODO: soft_delete not implemented
    async def soft_delete(self, data: List[Tuple[Id]]) -> None:
        return await super().soft_delete(data)
