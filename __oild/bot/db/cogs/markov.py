from dataclasses import dataclass
from typing import NamedTuple, List

from src.bot import MessageEntity
from __oild.bot.db.utils import Id, Entity, Table, DBConnection, inject_conn, Page

__all__ = [
    'MarkovEntity', 'MarkovRepository'
]


@dataclass
class MarkovEntity(Entity):
    __table_name__ = "cogs.markov"

    guild_id: Id
    context: str
    follows: str
    frequency: int = 1


class MarkovRepository(Table[MarkovEntity]):
    def __init__(self) -> None:
        super().__init__(entity=MarkovEntity)

    @inject_conn
    async def insert(self, conn: DBConnection, data: MarkovEntity) -> None:
        await conn.execute("""
            INSERT INTO cogs.markov AS m (guild_id, context, follows, frequency)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (guild_id, context, follows) DO UPDATE
                SET frequency = m.frequency + 1
        """, data.guild_id, data.context, data.follows, data.frequency)

    Next = NamedTuple('Next', [('follows', str), ('frequency', int)])

    @inject_conn
    async def find_random_next(self, conn: DBConnection, guild_id: Id, context: str) -> List["MarkovRepository.Next"]:
        rows = await conn.fetch("""
            SELECT follows, frequency
            FROM cogs.markov 
            WHERE guild_id = $1 AND
                  context = $2
        """, guild_id, context)
        return [self.Next(*row.values()) for row in rows]

    @inject_conn
    async def truncate(self, conn: DBConnection) -> None:
        await conn.execute("""
            TRUNCATE TABLE cogs.markov
        """)

    @inject_conn
    async def find_training_messages(self, conn: DBConnection, guild_id: int) -> Page[MessageEntity]:
        cursor = await conn.cursor(f"""
            SELECT m.*
            FROM server.messages m
            INNER JOIN server.channels c on c.id = m.channel_id
            INNER JOIN server.users u on u.id = m.author_id
            WHERE guild_id = $1 AND
                  NOT m.is_command AND
                  NOT u.is_bot
        """, guild_id)
        return Page[MessageEntity](cursor, MessageEntity)
