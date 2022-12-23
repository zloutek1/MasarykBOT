from dataclasses import dataclass
from typing import List, Tuple

from bot.db.utils import DBConnection, Id, Entity, Table, inject_conn



@dataclass
class LeaderboardFilter:
    guild_id: Id
    ignored_users: List[Id]
    include_channel_ids: List[Id]
    exclude_channel_ids: List[Id]



@dataclass
class LeaderboardEntity(Entity):
    __table_name__ = "cogs.leaderboard"

    row_no: int
    author_id: Id
    author: str
    sent_total: int



class LeaderboardRepository(Table[LeaderboardEntity]):
    tmp_table = "ldb_lookup"


    def __init__(self) -> None:
        super().__init__(entity=LeaderboardEntity)


    @inject_conn
    async def get_data(self, conn: DBConnection, user_id: int, filters: LeaderboardFilter) -> Tuple[List[LeaderboardEntity], List[LeaderboardEntity]]:
        await self.preselect(filters, conn=conn)
        return (
            await self.get_top10(conn=conn),
            await self.get_around(user_id, conn=conn)
        )


    @inject_conn
    async def preselect(self, conn: DBConnection, filters: LeaderboardFilter) -> None:
        await conn.execute(f"DROP TABLE IF EXISTS ldb_lookup")
        await conn.execute(f"""
            CREATE TEMPORARY TABLE IF NOT EXISTS ldb_lookup AS
                SELECT
                    ROW_NUMBER() OVER (ORDER BY sent_total DESC) as row_no, *
                FROM (
                    SELECT
                        author_id,
                        author.name AS author,
                        SUM(messages_sent) AS sent_total
                    FROM cogs.leaderboard
                    INNER JOIN server.users AS author
                        ON author_id = author.id
                    INNER JOIN server.channels AS channel
                        ON channel_id = channel.id
                    WHERE guild_id = $1::bigint AND
                          author_id <> ALL($2::bigint[]) AND
                          (
                              cardinality($3::bigint[]) = 0 OR 
                              channel_id = ANY($3::bigint[])
                          ) AND
                          channel_id <> ALL($4::bigint[])
                    GROUP BY author_id, author.name
                    ORDER BY sent_total DESC
                ) AS lookup
        """, filters.guild_id, filters.ignored_users, filters.include_channel_ids, filters.exclude_channel_ids)


    @inject_conn
    async def get_top10(self, conn: DBConnection) -> List[LeaderboardEntity]:
        rows = await conn.fetch(f"SELECT * FROM ldb_lookup LIMIT 10")
        return [LeaderboardEntity.convert(row) for row in rows]


    @inject_conn
    async def get_around(self, conn: DBConnection, id: Id) -> List[LeaderboardEntity]:
        rows = await conn.fetch(f"""
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
        """, id)
        return [LeaderboardEntity.convert(row) for row in rows]
