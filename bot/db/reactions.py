import asyncio
import logging
from collections import Counter
from datetime import datetime
from typing import List, Optional, Tuple, cast

from bot.db.utils import (Crud, DBConnection, FromMessageMapper, Id, Mapper,
                          Pool, Record, Table, WrappedCallable, withConn)
from disnake import Emoji, Message, PartialEmoji, Reaction

log = logging.getLogger(__name__)
Columns = Tuple[Id, Id, List[Id], datetime]

class ReactionDao(Table, Crud[Columns], Mapper[Reaction, Columns], FromMessageMapper[Columns]):
    @staticmethod
    async def prepare_one(reaction: Reaction) -> Columns:
        user_ids = await ReactionDao.get_user_ids(reaction)
        emoji_id = ReactionDao.get_emoji_id(reaction)
        created_at = reaction.message.created_at.replace(tzinfo=None)

        return (reaction.message.id, emoji_id, user_ids, created_at)

    async def prepare(self, reactions: List[Reaction]) -> List[Columns]:
        return [await self.prepare_one(reaction) for reaction in reactions]

    async def prepare_from_message(self, message: Message) -> List[Columns]:
        return await self.prepare(message.reactions)

    @withConn
    async def select(self, conn: DBConnection, data: Tuple[Id, Id]) -> List[Record]:
        return await conn.fetch("""
            SELECT * FROM server.reactions WHERE message_id=$1 AND emoji_id=$2
        """, data)

    @withConn
    async def insert(self, conn: DBConnection, data: List[Columns]) -> None:
        await conn.executemany("""
            INSERT INTO server.reactions AS r (message_id, emoji_id, member_ids, created_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (message_id, emoji_id) DO UPDATE
                SET member_ids=$3,
                    created_at=$4,
                    edited_at=NOW()
                WHERE r.member_ids<>excluded.member_ids OR
                      r.created_at<>excluded.created_at
        """, data)

    @withConn
    async def update(self, conn: DBConnection, data: List[Columns]) -> None:
        insert = cast(WrappedCallable, self.insert)
        await insert.__wrapped__(self, conn, data)

    @withConn
    async def soft_delete(self, conn: DBConnection, ids: List[Tuple[Id]]) -> None:
        await conn.executemany("""
            UPDATE server.reactions
            SET deleted_at=NOW()
            WHERE message_id = $1 AND emoji_id=$2;
        """, ids)

    @staticmethod
    async def get_user_ids(reaction: Reaction) -> List[Id]:
        try:
            return await reaction.users().map(lambda member: member.id).flatten()
        except asyncio.TimeoutError:
            log.warn("fetching users from reaction %s timed out (%s, %s)",
                     reaction.emoji,
                     reaction.message.channel,
                     reaction.message.id)
            return []

    @staticmethod
    def get_emoji_id(reaction: Reaction) -> Id:
        if isinstance(emote := reaction.emoji, (Emoji, PartialEmoji)):
            assert emote.id, "Emoji has to have an id"
            return emote.id
        return sum(map(ord, emote))
