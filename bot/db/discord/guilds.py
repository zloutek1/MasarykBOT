
from datetime import datetime
from typing import Optional, Sequence, Tuple

from discord import Guild

from bot.db.tables import GUILDS
from bot.db.utils import (Crud, DBConnection, Id, Mapper, Url)



Columns = Tuple[Id, str, Optional[Url], datetime]



class GuildMapper(Mapper[Guild, Columns]):
    async def map(self, obj: Guild) -> Columns:
        guild = obj
        icon_url = str(guild.icon.url) if guild.icon else None
        created_at = guild.created_at.replace(tzinfo=None)
        return (guild.id, guild.name, icon_url, created_at)



class GuildDao(Crud[Columns]):
    def __init__(self) -> None:
        super().__init__(table_name=GUILDS)

    async def insert(self, conn: DBConnection, data: Sequence[Columns]) -> None:
        await conn.executemany(f"""
            INSERT INTO {self.table_name} AS g (id, name, icon_url, created_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE
                SET name=$2,
                    icon_url=$3,
                    created_at=$4,
                    edited_at=NOW()
                WHERE g.name<>excluded.name OR
                        g.icon_url<>excluded.icon_url OR
                        g.created_at<>excluded.created_at
        """, data)