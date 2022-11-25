from typing import Sequence, Tuple

from bot.db.utils import (Crud, DBConnection, Id, withConn)
from bot.db.tables import MESSAGE_EMOJIS



Columns = Tuple[Id, Id, int]



class MessageEmojiRepository(Crud[Columns]):
    def __init__(self) -> None:
        super().__init__(table_name=MESSAGE_EMOJIS)


    @withConn
    async def insert(self, conn: DBConnection, data: Sequence[Columns]) -> None:
        await conn.executemany(f"""
            INSERT INTO {self.table_name} AS me (message_id, emoji_id, count)
            VALUES ($1, $2, $3)
            ON CONFLICT (message_id, emoji_id) DO UPDATE
                SET count=$3,
                    edited_at=NOW()
                WHERE me.count<>excluded.count
        """, data)


    @withConn
    async def soft_delete(self, conn: DBConnection, data: Sequence[Tuple[Id]]) -> None:
        # TODO: not implemented
        raise NotImplementedError