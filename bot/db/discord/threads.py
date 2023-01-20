from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from discord import Thread

from bot.db.utils import Entity, Id, Mapper, Crud, inject_conn, DBConnection



@dataclass
class ThreadEntity(Entity):
    __table_name__ = "server.messages"

    parent_id: Id
    id: Id
    name: str
    created_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None



class ThreadMapper(Mapper[Thread, ThreadEntity]):
    async def map(self, obj: Thread) -> ThreadEntity:
        thread = obj
        archived_at = thread.archive_timestamp.replace(tzinfo=None) if thread.archived else None
        created_at = (
            thread.created_at.replace(tzinfo=None)
            if thread.created_at else
            (await thread.fetch_message(thread.id)).created_at.replace(tzinfo=None)
        )
        return ThreadEntity(thread.parent_id, thread.id, thread.name, created_at, archived_at)



class ThreadRepository(Crud[ThreadEntity]):
    def __init__(self) -> None:
        super().__init__(entity=ThreadEntity)


    @inject_conn
    async def insert(self, conn: DBConnection, data: ThreadEntity) -> None:
        await conn.execute(f"""
            INSERT INTO server.threads AS ch (parent_id, id, name, created_at, archived_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE
                SET name=$3,
                    created_at=$4,
                    archived_at=$5,
                    edited_at=NOW()
                WHERE ch.name<>excluded.name OR
                      ch.created_at<>excluded.created_at OR
                      ch.archived_at<>excluded.archived_at
        """, data.parent_id, data.id, data.name, data.created_at, data.archived_at)
