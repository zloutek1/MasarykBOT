from typing import List, Tuple

from .utils import DBConnection, Id, Record, Table, inject_conn
from .tables import LEADERBOARD, USERS, CHANNELS

Filters = Tuple[Id, List[Id], List[Id], List[Id]]


class LeaderboardRepository(Table):
    tmp_table = "ldb_lookup"

    def __init__(self) -> None:
        super().__init__(table_name=LEADERBOARD)

    @inject_conn
    async def preselect(self, conn: DBConnection, filters: Filters) -> None:
        guild_id, ignored_users, include_channel_ids, exclude_channel_ids = filters

        await conn.execute(f"DROP TABLE IF EXISTS {self.tmp_table}")
        await conn.execute(f"""
            CREATE TEMPORARY TABLE IF NOT EXISTS {self.tmp_table} AS
                SELECT
                    ROW_NUMBER() OVER (ORDER BY sent_total DESC), *
                FROM (
                    SELECT
                        author_id,
                        author.names[1] AS author,
                        SUM(messages_sent) AS sent_total
                    FROM {self.table_name}
                    INNER JOIN {USERS} AS author
                        ON author_id = author.id
                    INNER JOIN {CHANNELS} AS channel
                        ON channel_id = channel.id
                    WHERE guild_id = $1::bigint AND
                          author_id<>ALL($2::bigint[]) AND
                          channel_id=ANY($3::bigint[]) AND
                          channel_id<>ALL($4::bigint[])
                    GROUP BY author_id, author.names
                    ORDER BY sent_total DESC
                ) AS lookup
        """, guild_id, ignored_users, include_channel_ids, exclude_channel_ids)

    @inject_conn
    async def get_top10(self, conn: DBConnection) -> List[Record]:
        return await conn.fetch(f"SELECT * FROM {self.tmp_table} LIMIT 10")

    @inject_conn
    async def get_around(self, conn: DBConnection, id: Id) -> List[Record]:
        return await conn.fetch(f"""
            WITH desired_count AS (
                SELECT sent_total
                FROM {self.tmp_table}
                WHERE author_id = $1
            )

            (   SELECT *
                FROM {self.tmp_table}
                WHERE sent_total >= (SELECT * FROM desired_count) AND
                      author_id <> $1
                ORDER BY sent_total LIMIT 2
            ) UNION (
                SELECT *
                FROM {self.tmp_table}
                WHERE sent_total = (SELECT * FROM desired_count) AND
                      author_id = $1 LIMIT 1
            ) UNION (
                SELECT *
                FROM {self.tmp_table}
                WHERE sent_total < (SELECT * FROM desired_count) AND
                      author_id <> $1 LIMIT 2
            ) ORDER BY sent_total DESC
        """, id)
