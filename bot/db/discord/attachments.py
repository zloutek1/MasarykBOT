import inject
from typing import List, Optional, Sequence, Tuple

from discord import Attachment, Message

from bot.db.tables import ATTACHMENTS
from bot.db.utils import (Crud, DBConnection, Id, Mapper, Url, withConn)



Columns = Tuple[Optional[Id], Id, str, Url]



class AttachmentMapper(Mapper[Attachment, Columns]):
    async def map(self, obj: Attachment) -> Columns:
        attachment = obj
        return (None, attachment.id, attachment.filename, attachment.url)



class AttachmentRepository(Crud[Columns]):
    def __init__(self) -> None:
        super().__init__(table_name=ATTACHMENTS)


    @withConn
    async def insert(self, conn: DBConnection, data: Sequence[Columns]) -> None:
        await conn.executemany(f"""
            INSERT INTO {self.table_name} AS a (message_id, id, filename, url)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE
                SET filename=$3,
                    url=$4
                WHERE a.filename<>excluded.filename OR
                        a.url<>excluded.url
        """, data)


    @withConn
    async def soft_delete(self, conn: DBConnection, data: Sequence[Tuple[Id]]) -> None:
        # TODO: soft_delete not implemented
        raise NotImplemented
