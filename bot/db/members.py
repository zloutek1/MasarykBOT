from datetime import datetime
from typing import List, Optional, Tuple, Union, cast, overload

from bot.db.utils import (Crud, DBConnection, FromMessageMapper, Id, Mapper,
                          Record, Table, Url, WrappedCallable, withConn)
from disnake import Member, Message, User

Columns = Tuple[Id, str, Optional[Url], bool, datetime]

class Users(Table, Crud[Columns], Mapper[Union[User, Member], Columns], FromMessageMapper[Columns]):
    @staticmethod
    async def prepare_one(user: Union[User, Member]) -> Columns:
        avatar_url = str(user.avatar.url) if user.avatar else None
        created_at = user.created_at.replace(tzinfo=None)
        return (user.id, user.name, avatar_url, user.bot, created_at)

    async def prepare(self, members: List[Union[User, Member]]) -> List[Columns]:
        return [await self.prepare_one(member) for member in members]

    async def prepare_from_message(self, message: Message) -> List[Columns]:
        return [await self.prepare_one(message.author)]

    @withConn
    async def select(self, conn: DBConnection, user_id: Id) -> List[Record]:
        return await conn.fetch("""
            SELECT * FROM server.users WHERE id=$1
        """, user_id)

    @withConn
    async def insert(self, conn: DBConnection, data: List[Columns]) -> None:
        await conn.executemany("""
            INSERT INTO server.users AS u (id, names, avatar_url, is_bot, created_at)
            VALUES ($1, ARRAY[$2], $3, $4, $5)
            ON CONFLICT (id) DO UPDATE
                SET names=ARRAY(
                        SELECT DISTINCT e
                        FROM unnest(array_prepend($2::varchar, u.names)) AS a(e)
                    ),
                    avatar_url=$3,
                    is_bot=$4,
                    created_at=$5,
                    edited_at=NOW()
                WHERE $2<>ANY(excluded.names) OR
                        u.avatar_url<>excluded.avatar_url OR
                        u.is_bot<>excluded.is_bot OR
                        u.created_at<>excluded.created_at
        """, data)

    @withConn
    async def update(self, conn: DBConnection, data: List[Columns]) -> None:
        insert = cast(WrappedCallable, self.insert)
        await insert.__wrapped__(self, conn, data)

    @withConn
    async def soft_delete(self, conn: DBConnection, ids: List[Tuple[Id]]) -> None:
        await conn.executemany("""
            UPDATE server.users
            SET deleted_at=NOW()
            WHERE id = $1;
        """, ids)
