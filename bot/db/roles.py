from datetime import datetime
from typing import List, Tuple, cast

from bot.db.utils import (Crud, DBConnection, Id, Mapper, Record, Table,
                          WrappedCallable, withConn)
from disnake import Role

Columns = Tuple[Id, Id, str, str, datetime]

class Roles(Table, Crud[Columns], Mapper[Role, Columns]):
    @staticmethod
    async def prepare_one(role: Role) -> Columns:
        created_at = role.created_at.replace(tzinfo=None)
        return (role.guild.id, role.id, role.name, hex(role.color.value), created_at)

    async def prepare(self, roles: List[Role]) -> List[Columns]:
        return [await self.prepare_one(role) for role in roles]

    @withConn
    async def select(self, conn: DBConnection, role_id: Id) -> List[Record]:
        return await conn.fetch("""
            SELECT * FROM server.roles WHERE id=$1
        """, role_id)

    @withConn
    async def insert(self, conn: DBConnection, data: List[Columns]) -> None:
        await conn.executemany("""
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
        """, data)

    @withConn
    async def update(self, conn: DBConnection, data: List[Columns]) -> None:
        insert = cast(WrappedCallable, self.insert)
        await insert.__wrapped__(self, conn, data)

    @withConn
    async def soft_delete(self, conn: DBConnection, ids: List[Tuple[Id]]) -> None:
        await conn.executemany("UPDATE server.roles SET deleted_at=NOW() WHERE id = $1;", ids)
