import inject
from typing import List, Optional, Sequence, Tuple

from discord import Attachment, Message

from bot.db.tables import ATTACHMENTS
from bot.db.utils import (Crud, DBConnection, Id, Mapper, Url)



Columns = Tuple[Optional[Id], Id, str, Url]



class AttachmentMapper(Mapper[Attachment, Columns]):
    async def map(self, obj: Attachment) -> Columns:
        attachment = obj
        return (None, attachment.id, attachment.filename, attachment.url)



class MessageAttachmentsMapper(Mapper[Message, Sequence[Columns]]):
    attachment_mapper = inject.attr(AttachmentMapper)

    async def map(self, obj: Message) -> Sequence[Columns]:
        message = obj
        result: List[Columns] = []
        for attachment in message.attachments:
            (_, attachment_id, filename, url) = await self.attachment_mapper.map(attachment)
            result.append((message.id, attachment_id, filename, url))
        return result



class AttachmentDao(Crud[Columns]):
    def __init__(self) -> None:
        super().__init__(table_name=ATTACHMENTS)


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


    async def soft_delete(self, conn: DBConnection, data: Sequence[Tuple[Id]]) -> None:
        # TODO: soft_delete not implemented
        raise NotImplemented
