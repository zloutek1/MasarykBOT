from dataclasses import dataclass, astuple
from typing import Optional, Sequence, Tuple

from discord import Attachment

from bot.db.utils import Entity, Mapper, Id, Crud, inject_conn, DBConnection



@dataclass
class AttachmentEntity(Entity):
    message_id: Optional[Id]
    id: Id
    filename: str
    url: str



class AttachmentMapper(Mapper[Attachment, AttachmentEntity]):
    async def map(self, obj: Attachment) -> AttachmentEntity:
        attachment = obj
        return AttachmentEntity(None, attachment.id, attachment.filename, attachment.url)



class AttachmentRepository(Crud[AttachmentEntity]):
    def __init__(self) -> None:
        super().__init__(table_name="server.attachments")


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
        """, astuple(data))


    @inject_conn
    async def soft_delete(self, conn: DBConnection, id: Id) -> None:
        # TODO: soft_delete not implemented
        raise NotImplemented
