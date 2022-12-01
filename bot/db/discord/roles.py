from dataclasses import dataclass, astuple
from datetime import datetime
from typing import Optional

from discord import Role

from bot.db.utils import (Crud, DBConnection, Id, Mapper, inject_conn, Entity)



@dataclass
class RoleEntity(Entity):
    __table_name__ = "server.role"

    guild_id: Id
    id: Id
    name: str
    color: str
    created_at: datetime
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None



class RoleMapper(Mapper[Role, RoleEntity]):
    async def map(self, obj: Role) -> RoleEntity:
        role = obj
        created_at = role.created_at.replace(tzinfo=None)
        return RoleEntity(role.guild.id, role.id, role.name, hex(role.color.value), created_at)


class RoleRepository(Crud[RoleEntity]):
    def __init__(self) -> None:
        super().__init__(entity=RoleEntity)


    @inject_conn
    async def insert(self, conn: DBConnection, data: RoleEntity) -> None:
        await conn.execute(f"""
            INSERT INTO server.roles AS r (guild_id, id, name, color, created_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE
                SET name=$3,
                    color=$4,
                    created_at=$5,
                    edited_at=NOW()
                WHERE r.name<>excluded.name OR
                        r.color<>excluded.color OR
                        r.created_at<>excluded.created_at
        """, astuple(data))
