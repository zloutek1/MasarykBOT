from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from discord import Reaction

from bot.db.utils import Crud, DBConnection, Id, Mapper, inject_conn, Entity
from bot.utils import get_emoji_id



@dataclass
class ReactionEntity(Entity):
    message_id: Id
    emoji_id: Id
    user_ids: List[Id]
    created_at: datetime
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None



class ReactionMapper(Mapper[Reaction, ReactionEntity]):
    async def map(self, obj: Reaction) -> ReactionEntity:
        reaction = obj
        user_ids = [user.id async for user in reaction.users()]
        emoji_id = get_emoji_id(reaction.emoji)
        created_at = reaction.message.created_at.replace(tzinfo=None)
        return ReactionEntity(reaction.message.id, emoji_id, user_ids, created_at)



class ReactionRepository(Crud[ReactionEntity]):
    def __init__(self) -> None:
        super().__init__(entity=ReactionEntity)


    @inject_conn
    async def insert(self, conn: DBConnection, data: ReactionEntity) -> None:
        await conn.execute(f"""
            INSERT INTO server.reactions AS r (message_id, emoji_id, member_ids, created_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (message_id, emoji_id) DO UPDATE
                SET member_ids=$3,
                    created_at=$4,
                    edited_at=NOW()
                WHERE r.member_ids<>excluded.member_ids OR
                      r.created_at<>excluded.created_at
        """, data.message_id, data.emoji_id, data.user_ids, data.created_at)


    @inject_conn
    async def soft_delete(self, conn: DBConnection, id: Id) -> None:
        await conn.execute(f"""
            UPDATE server.reactions
            SET deleted_at=NOW()
            WHERE message_id = $1 AND emoji_id=$2;
        """, (id,))
