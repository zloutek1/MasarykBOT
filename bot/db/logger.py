from datetime import datetime
from typing import Any, Optional, Tuple

from .utils import DBConnection, Id, Record, Table, inject_conn
from .tables import LOGGER


class LoggerRepository(Table):
    def __init__(self) -> None:
        super().__init__(table_name=LOGGER)

    @inject_conn
    async def begin_process(self, conn: DBConnection, data: Tuple[Id, datetime, datetime]) -> None:
        channel_id, from_date, to_date = data
        await conn.execute(f"""
            INSERT INTO {LOGGER} VALUES ($1, $2, $3, NULL)
            ON CONFLICT (channel_id, from_date) DO NOTHING
        """, channel_id, from_date, to_date)

    @inject_conn
    async def end_process(self, conn: DBConnection, data: Tuple[Id, datetime, datetime]) -> None:
        channel_id, from_date, to_date = data
        await conn.execute(f"""
            UPDATE {LOGGER} 
            SET finished_at=NOW()
            WHERE channel_id=$1 AND from_date=$2 AND to_date=$3
        """, channel_id, from_date, to_date)

    @inject_conn
    async def find_last_process(self, conn: DBConnection, channel_id: Id) -> Optional[Record]:
        return await conn.fetchrow(f"""
            SELECT * 
            FROM {LOGGER}
            WHERE channel_id=$1
            ORDER BY to_date DESC
        """, channel_id)

    @inject_conn
    async def find_updatable_processes(self, conn: DBConnection) -> list[Record]:
        return await conn.fetch(f"""
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