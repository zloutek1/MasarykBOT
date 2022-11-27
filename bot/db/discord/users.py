from datetime import datetime
from typing import Optional, Sequence, Tuple, Union

from discord import Member, User

from bot.db.utils import (Crud, DBConnection, Id, Mapper, Url, inject_conn)
from bot.db.tables import USERS

Columns = Tuple[Id, str, Optional[Url], bool, datetime]


class UserMapper(Mapper[Union[User, Member], Columns]):
    async def map(self, obj: Union[User, Member]) -> Columns:
        user = obj
        avatar_url = str(user.avatar.url) if user.avatar else None
        created_at = user.created_at.replace(tzinfo=None)
        return user.id, user.name, avatar_url, user.bot, created_at


class UserRepository(Crud[Columns]):
    def __init__(self) -> None:
        super().__init__(table_name=USERS)

    @inject_conn
    async def insert(self, conn: DBConnection, data: Sequence[Columns]) -> None:
        await conn.executemany(f"""
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
