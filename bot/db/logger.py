from datetime import datetime
from typing import Any, Optional, Tuple

from .utils import DBConnection, Id, Record, Table, withConn
from .tables import LOGGER


class LoggerRepository(Table):
    def __init__(self) -> None:
        super().__init__(table_name=LOGGER)

    def with_process(self, data: Tuple[Id, datetime, datetime]) -> "ProcessContext":
        return ProcessContext(self, data)

    @withConn
    async def begin_process(self, conn: DBConnection, data: Tuple[Id, datetime, datetime]) -> None:
        channel_id, from_date, to_date = data
        await conn.execute(f"""
            INSERT INTO {LOGGER} VALUES ($1, $2, $3, NULL)
            ON CONFLICT (channel_id, from_date) DO NOTHING
        """, channel_id, from_date, to_date)

    @withConn
    async def end_process(self, conn: DBConnection, data: Tuple[Id, datetime, datetime]) -> None:
        channel_id, from_date, to_date = data
        await conn.execute(f"""
            UPDATE {LOGGER} 
            SET finished_at=NOW()
            WHERE channel_id=$1 AND from_date=$2 AND to_date=$3
        """, channel_id, from_date, to_date)

    @withConn
    async def find_last_process(self, conn: DBConnection, channel_id: Id) -> Optional[Record]:
        return await conn.fetchrow(f"""
            SELECT * 
            FROM {LOGGER}
            WHERE channel_id=$1
            ORDER BY to_date DESC
        """, channel_id)

    @withConn
    async def find_updatable_processes(self, conn: DBConnection) -> list[Record]:
        return await conn.fetch(f"""
            SELECT channel_id, MAX(to_date)
            FROM {LOGGER}
            GROUP BY channel_id
        """)


class ProcessContext:
    def __init__(self, cls: LoggerRepository, data: Tuple[Id, datetime, datetime]) -> None:
        self.parent = cls
        self.data = data

    async def __aenter__(self) -> None:
        await self.parent.begin_process(self.data)

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.parent.end_process(self.data)
