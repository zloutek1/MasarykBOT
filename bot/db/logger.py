from datetime import datetime
from types import TracebackType
from typing import List, Optional, Tuple, Type, cast

from .utils import DBConnection, Id, Record, Table, WrappedCallable, withConn
from .tables import LOGGER, MESSAGES

class LoggerDao(Table):
    @withConn
    async def select(self, conn: DBConnection, channel_id: Id) -> List[Record]:
        return await conn.fetch(f"""
            SELECT *
            FROM {LOGGER}
            WHERE channel_id = $1
        """, channel_id)

    @withConn
    async def select_latest_backup_message_ids(self, conn: DBConnection) -> List[Record]:
        return await conn.fetch(f"""
            SELECT channel_id, MAX(id) as id
            FROM {MESSAGES}
            GROUP BY channel_id;
        """)

    @withConn
    async def start_process(
        self,
        conn: DBConnection,
        data: Tuple[Id, datetime, datetime]
    ) -> None:
        channel_id, from_date, to_date = data
        await conn.execute(f"""
            INSERT INTO {LOGGER} VALUES ($1, $2, $3, NULL)
            ON CONFLICT (channel_id, from_date) DO NOTHING
        """, channel_id, from_date, to_date)

    @withConn
    async def mark_process_finished(
        self,
        conn: DBConnection,
        data: Tuple[Id, datetime, datetime, bool]
    ) -> None:
        channel_id, from_date, to_date, is_first_week = data
        if is_first_week:
            await conn.execute(f"""
                UPDATE {LOGGER}
                SET finished_at = NOW()
                WHERE channel_id = $1 AND
                      finished_at IS NULL
            """, channel_id)
        else:
            async with conn.transaction():
                await conn.execute(f"""
                    DELETE FROM {LOGGER}
                    WHERE channel_id = $1 AND
                          from_date = $2 AND
                          to_date = $3
                    """, channel_id, from_date, to_date)
                await conn.execute(f"""
                    UPDATE {LOGGER}
                    SET to_date = $3,
                        finished_at = NOW()
                    WHERE channel_id = $1 AND
                          to_date = $2 AND
                          finished_at IS NOT NULL
                          """, channel_id, from_date, to_date)

    def process(self,
                channel_id: Id,
                from_date: datetime,
                to_date: datetime,
                is_first_week: bool=False,
                conn: Optional[DBConnection]=None
    ) -> "LoggerDao.Process":
        return self.Process(
            self,
            channel_id,
            from_date,
            to_date,
            is_first_week,
            conn)

    class Process:
        def __init__(
            self,
            cls: "LoggerDao",
            channel_id: Id,
            from_date: datetime,
            to_date: datetime,
            is_first_week: bool=False,
            conn: Optional[DBConnection]=None
        ):
            self.parent = cls
            self.conn = conn

            self.channel_id = channel_id
            self.from_date = from_date
            self.to_date = to_date
            self.is_first_week = is_first_week

        async def __aenter__(self) -> None:
            wrapped = cast(WrappedCallable, self.parent.start_process)
            data = (self.channel_id, self.from_date, self.to_date)

            if self.conn is not None:
                await wrapped(self.parent, self.conn, data=data)
                return
            await self.parent.start_process(data)

        async def __aexit__(self,
                            exc_type: Optional[Type[BaseException]],
                            exc: Optional[BaseException],
                            traceback: Optional[TracebackType]
        ) -> None:
            wrapped = cast(WrappedCallable, self.parent.mark_process_finished)
            data = (self.channel_id, self.from_date, self.to_date, self.is_first_week)

            if self.conn:
                await wrapped(self.parent, self.conn, data)
            await self.parent.mark_process_finished(data)
