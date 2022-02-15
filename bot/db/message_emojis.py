from collections import Counter
from datetime import datetime
from typing import List, Optional, Tuple, cast

from bot.db.emojis import EmojiDao
from bot.db.utils import (Crud, DBConnection, FromMessageMapper, Id, Mapper,
                          Pool, Record, Table, WrappedCallable, withConn)
from disnake import Message

Columns = Tuple[Id, Id, int]

class MessageEmojiDao(Table, Crud[Columns], FromMessageMapper[Columns]):
    def __init__(self, pool: Pool):
        super().__init__(pool)
        self.emojis = EmojiDao(self.pool)

    async def prepare_from_message(self, message: Message) -> List[Columns]:
        emojis = await self.emojis._prepare_from_message_content(message)
        emoji_ids = [emoji[0] for emoji in emojis]
        return [(message.id, emoji_id, count)
                for (emoji_id, count) in Counter(emoji_ids).items()]

    @withConn
    async def select(self, conn: DBConnection, emoji_id: Id) -> List[Record]:
        return await conn.fetch("""
            SELECT * FROM server.message_emojis WHERE message_id=$1 AND emoji_id=$2
        """, emoji_id)

    @withConn
    async def insert(self, conn: DBConnection, data: List[Columns]) -> None:
        await conn.executemany("""
            INSERT INTO server.message_emojis AS me (message_id, emoji_id, count)
            VALUES ($1, $2, $3)
            ON CONFLICT (message_id, emoji_id) DO UPDATE
                SET count=$3,
                    edited_at=NOW()
                WHERE me.count<>excluded.count
        """, data)

    @withConn
    async def update(self, conn: DBConnection, data: List[Columns]) -> None:
        insert = cast(WrappedCallable, self.insert)
        await insert.__wrapped__(self, conn, data)
