from dataclasses import dataclass
from typing import Optional

from __oild.bot.db.utils import Entity, Mapper, Id, Crud, inject_conn, DBConnection
from src.bot import MessageAttachment


@dataclass
class AttachmentEntity(Entity):
    __table_name__ = "server.attachment"

    message_id: Optional[Id]
    id: Id
    filename: str
    url: str


class AttachmentMapper(Mapper[MessageAttachment, AttachmentEntity]):
    async def map(self, obj: MessageAttachment) -> AttachmentEntity:
        message, attachment = obj.message, obj.attachment
        return AttachmentEntity(None, attachment.id, attachment.filename, attachment.url)


class AttachmentRepository(Crud[AttachmentEntity]):
    def __init__(self) -> None:
        super().__init__(entity=AttachmentEntity)

    @inject_conn
    async def insert(self, conn: DBConnection, data: AttachmentEntity) -> None:
        await conn.execute(f"""
            INSERT INTO server.attachments AS a (message_id, id, filename, url)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE
                SET filename=$3,
                    url=$4
                WHERE a.filename<>excluded.filename OR
                        a.url<>excluded.url
        """, data.message_id, data.id, data.filename, data.url)

    @inject_conn
    async def soft_delete(self, conn: DBConnection, id: Id) -> None:
        # TODO: soft_delete not implemented
        raise NotImplemented
