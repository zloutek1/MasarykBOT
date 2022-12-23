from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from discord import Member, User

from bot.db.utils import (Crud, DBConnection, Id, Mapper, Url, inject_conn, Entity)



@dataclass
class UserEntity(Entity):
    __table_name__ = "server.user"

    id: Id
    name: str
    avatar_url: Url
    is_bot: bool
    created_at: datetime
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None



class UserMapper(Mapper[Union[User, Member], UserEntity]):
    async def map(self, obj: Union[User, Member]) -> UserEntity:
        user = obj
        avatar_url = str(user.avatar.url) if user.avatar else user.default_avatar.url
        created_at = user.created_at.replace(tzinfo=None)
        return UserEntity(user.id, user.name, avatar_url, user.bot, created_at)



class UserRepository(Crud[UserEntity]):
    def __init__(self) -> None:
        super().__init__(entity=UserEntity)


    @inject_conn
    async def insert(self, conn: DBConnection, data: UserEntity) -> None:
        await conn.execute(f"""
            INSERT INTO server.users AS u (id, name, avatar_url, is_bot, created_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE
                SET name=$2,
                    avatar_url=$3,
                    is_bot=$4,
                    created_at=$5,
                    edited_at=NOW()
                WHERE u.name<>excluded.name OR
                      u.avatar_url<>excluded.avatar_url OR
                      u.is_bot<>excluded.is_bot OR
                      u.created_at<>excluded.created_at
        """, data.id, data.name, data.avatar_url, data.is_bot, data.created_at)
