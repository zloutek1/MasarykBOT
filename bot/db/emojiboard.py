from typing import List, Optional, Tuple

from .utils import DBConnection, Id, Record, Table, withConn
from .tables import EMOJIBOARD, CHANNELS, EMOJIS

class EmojiboardDao(Table):
    @withConn
    async def select(
        self,
        conn: DBConnection,
        data: Tuple[Id, List[Id], Optional[Id], Optional[Id], Optional[Id]]
    ) -> List[Record]:
        guild_id, ignored_users, channel_id, author_id, emoji_id = data

        return await conn.fetch(f"""
            SELECT
                emoji.name,
                SUM(count) AS sent_total
            FROM {EMOJIBOARD}
            INNER JOIN {CHANNELS} AS channel
                ON channel_id = channel.id
            INNER JOIN {EMOJIS} AS emoji
                ON emoji_id = emoji.id
            WHERE guild_id = $1::bigint AND
                    author_id<>ALL($2::bigint[]) AND
                    ($3::bigint IS NULL OR channel_id = $3) AND
                    ($4::bigint IS NULL OR author_id = $4) AND
                    ($5::bigint IS NULL OR emoji_id = $5)
            GROUP BY emoji.name
            ORDER BY sent_total DESC
            LIMIT 10
        """, guild_id, ignored_users, channel_id, author_id, emoji_id)

