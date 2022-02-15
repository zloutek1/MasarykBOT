
from datetime import date, datetime
from typing import List, Optional, Tuple

from bot.db.utils import DBConnection, Id, Record, Table, withConn


class ActivityDao(Table):
    @withConn
    async def select(
        self,
        conn: DBConnection,
        data: Tuple[Id, Optional[Id], Optional[Id], date, date]
    ) -> List[Record]:

        guild_id, channel_id, author_id, from_date, to_date = data
        return await conn.fetch("""
           SELECT
                date_trunc('day', m.created_at) as "day",
                count(*) as "messages_sent"
            FROM server.messages AS m
            INNER JOIN server.channels AS ch
               ON m.channel_id = ch.id
            WHERE guild_id = $1 AND
                  (channel_id = $2 OR $2 IS NULL) AND
                  (author_id = $3 OR $3 IS NULL) AND
                  $4 <= m.created_at AND m.created_at <= $5 AND
                  m.deleted_at IS NULL
            GROUP BY 1
            ORDER BY 1
        """, guild_id, channel_id, author_id, from_date, to_date)
