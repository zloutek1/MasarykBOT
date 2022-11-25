from datetime import datetime
from typing import Sequence, Tuple

from discord import Role

from bot.db.utils import (Crud, DBConnection, Id, Mapper, withConn)
from bot.db.tables import ROLES



Columns = Tuple[Id, Id, str, str, datetime]



class RoleMapper(Mapper[Role, Columns]):
    async def map(self, obj: Role) -> Columns:
        role = obj
        created_at = role.created_at.replace(tzinfo=None)
        return (role.guild.id, role.id, role.name, hex(role.color.value), created_at)



class RoleRepository(Crud[Columns]):
    def __init__(self) -> None:
        super().__init__(table_name=ROLES)


    @withConn
    async def insert(self, conn: DBConnection, data: Sequence[Columns]) -> None:
        await conn.executemany(f"""
            INSERT INTO {ROLES} AS r (guild_id, id, name, color, created_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE
                SET name=$3,
                    color=$4,
                    created_at=$5,
                    edited_at=NOW()
                WHERE r.name<>excluded.name OR
                        r.color<>excluded.color OR
                        r.created_at<>excluded.created_at
        """, data)