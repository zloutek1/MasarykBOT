from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple, NamedTuple, List

from bot.db.utils import Id, Entity, Table, DBConnection, inject_conn

__all__ = [
    'LoggerEntity', 'LoggerRepository'
]


@dataclass
class LoggerEntity(Entity):
    __table_name__ = "cogs.logger"

    channel_id: Id
    from_date: datetime
    to_date: datetime
    finished_at: Optional[datetime] = None



class LoggerRepository(Table[LoggerEntity]):
    def __init__(self) -> None:
        super().__init__(entity=LoggerEntity)


    @inject_conn
    async def begin_process(self, conn: DBConnection, data: Tuple[Id, datetime, datetime]) -> None:
        channel_id, from_date, to_date = data
        await conn.execute(f"""
            INSERT INTO cogs.logger VALUES ($1, $2, $3, NULL)
            ON CONFLICT (channel_id, from_date) DO NOTHING
        """, channel_id, from_date, to_date)


    @inject_conn
    async def end_process(self, conn: DBConnection, data: Tuple[Id, datetime, datetime]) -> None:
        channel_id, from_date, to_date = data
        await conn.execute(f"""
            UPDATE cogs.logger
            SET finished_at=NOW()
            WHERE channel_id=$1 AND from_date=$2 AND to_date=$3
        """, channel_id, from_date, to_date)


    @inject_conn
    async def find_last_process(self, conn: DBConnection, channel_id: Id) -> Optional[LoggerEntity]:
        row = await conn.fetchrow(f"""
            SELECT * 
            FROM cogs.logger
            WHERE channel_id=$1
            ORDER BY to_date DESC
        """, channel_id)
        return LoggerEntity.convert(row) if row else None


    UpdatableProcesses = NamedTuple('UpdatableProcesses', [('channel_id', Id), ('to_date', datetime)])


    @inject_conn
    async def find_updatable_processes(self, conn: DBConnection) -> List["LoggerRepository.UpdatableProcesses"]:
        rows = await conn.fetch(f"""
            SELECT channel_id, to_date
            FROM (
                SELECT channel_id, MAX(to_date) as to_date
                FROM cogs.logger
                GROUP BY channel_id
            ) t
            INNER JOIN server.channels as c 
                ON c.id = t.channel_id
            WHERE t.to_date + interval '7 days' < now() AND
                  c.deleted_at IS NULL
        """)
        return [self.UpdatableProcesses(*row.values()) for row in rows]
