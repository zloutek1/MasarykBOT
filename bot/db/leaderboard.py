from typing import List, Optional, Tuple

from .utils import DBConnection, Id, Record, Table, withConn


class Leaderboard(Table):
    @withConn
    async def preselect(
        self,
        conn: DBConnection,
        data: Tuple[Id, List[Id], Optional[Id]]
    ) -> None:
        guild_id, ignored_users, channel_id = data

        await conn.execute("DROP TABLE IF EXISTS ldb_lookup")
        await conn.execute("""
            CREATE TEMPORARY TABLE IF NOT EXISTS ldb_lookup AS
                SELECT
                    ROW_NUMBER() OVER (ORDER BY sent_total DESC), *
                FROM (
                    SELECT
                        author_id,
                        author.names[1] AS author,
                        SUM(messages_sent) AS sent_total
                    FROM cogs.leaderboard
                    INNER JOIN server.users AS author
                        ON author_id = author.id
                    INNER JOIN server.channels AS channel
                        ON channel_id = channel.id
                    WHERE guild_id = $1::bigint AND
                            author_id<>ALL($2::bigint[]) AND
                            ($3::bigint IS NULL OR channel_id = $3)
                    GROUP BY author_id, author.names
                    ORDER BY sent_total DESC
                ) AS lookup
        """, guild_id, ignored_users, channel_id)

    @withConn
    async def get_top10(self, conn: DBConnection) -> List[Record]:
        return await conn.fetch("SELECT * FROM ldb_lookup LIMIT 10")

    @withConn
    async def get_around(self, conn: DBConnection, data: Tuple[Id]) -> List[Record]:
        author_id, *_ = data

        return await conn.fetch("""
            WITH desired_count AS (
                SELECT sent_total
                FROM ldb_lookup
                WHERE author_id = $1
            )

            (   SELECT *
                FROM ldb_lookup
                WHERE sent_total >= (SELECT * FROM desired_count) AND
                      author_id <> $1
                ORDER BY sent_total LIMIT 2
            ) UNION (
                SELECT *
                FROM ldb_lookup
                WHERE sent_total = (SELECT * FROM desired_count) AND
                      author_id = $1 LIMIT 1
            ) UNION (
                SELECT *
                FROM ldb_lookup
                WHERE sent_total < (SELECT * FROM desired_count) AND
                      author_id <> $1 LIMIT 2
            ) ORDER BY sent_total DESC
        """, author_id)
