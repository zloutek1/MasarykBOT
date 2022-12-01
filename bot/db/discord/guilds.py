from dataclasses import dataclass, astuple
from datetime import datetime
from typing import Optional

from discord import Guild

from bot.db.utils import Crud, DBConnection, Id, Mapper, Url, inject_conn, Entity



@dataclass
class GuildEntity(Entity):
    id: Id
    name: str
    url: Optional[Url]
    created_at: datetime
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None



class GuildMapper(Mapper[Guild, GuildEntity]):
    async def map(self, obj: Guild) -> GuildEntity:
        guild = obj
        icon_url = str(guild.icon.url) if guild.icon else None
        created_at = guild.created_at.replace(tzinfo=None)
        return GuildEntity(guild.id, guild.name, icon_url, created_at)



class GuildRepository(Crud[GuildEntity]):
    def __init__(self) -> None:
        super().__init__(entity=GuildEntity)


    @inject_conn
    async def insert(self, conn: DBConnection, data: GuildEntity) -> None:
        await conn.execute(f"""
            INSERT INTO server.guilds AS g (id, name, icon_url, created_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE
                SET name=$2,
                    icon_url=$3,
                    created_at=$4,
                    edited_at=NOW()
                WHERE g.name<>excluded.name OR
                        g.icon_url<>excluded.icon_url OR
                        g.created_at<>excluded.created_at
        """, astuple(data))
