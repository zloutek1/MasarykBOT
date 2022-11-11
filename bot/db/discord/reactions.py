import logging
import inject
from datetime import datetime
from typing import List, Sequence, Tuple

from discord import Reaction, Message

from .emojis import emoji_hashcode
from bot.db.utils import (Crud, DBConnection, Id, Mapper)
from ..tables import REACTIONS



log = logging.getLogger(__name__)
Columns = Tuple[Id, Id, List[Id], datetime]



class ReactionMapper(Mapper[Reaction, Columns]):
    async def map(self, obj: Reaction) -> Columns:
        reaction = obj
        user_ids = [user.id async for user in reaction.users()]
        emoji_id = emoji_hashcode(reaction.emoji)
        created_at = reaction.message.created_at.replace(tzinfo=None)
        return (reaction.message.id, emoji_id, user_ids, created_at)



class MessageReactionsMapper(Mapper[Message, Sequence[Columns]]):
    reaction_mapper = inject.attr(ReactionMapper)
    
    async def map(self, obj: Message) -> Sequence[Columns]:
        message = obj
        return [await self.reaction_mapper.map(reaction) 
                for reaction in message.reactions]



class ReactionDao(Crud[Columns]):
    def __init__(self) -> None:
        super().__init__(table_name=REACTIONS)


    async def insert(self, conn: DBConnection, data: Sequence[Columns]) -> None:
        await conn.executemany(f"""
            INSERT INTO {self.table_name} AS r (message_id, emoji_id, member_ids, created_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (message_id, emoji_id) DO UPDATE
                SET member_ids=$3,
                    created_at=$4,
                    edited_at=NOW()
                WHERE r.member_ids<>excluded.member_ids OR
                      r.created_at<>excluded.created_at
        """, data)


    async def soft_delete(self, conn: DBConnection, data: Sequence[Tuple[Id]]) -> None:
        await conn.executemany(f"""
            UPDATE {self.table_name}
            SET deleted_at=NOW()
            WHERE message_id = $1 AND emoji_id=$2;
        """, data)
