from collections import Counter
from dataclasses import dataclass
import re
from typing import List, Optional, Tuple

from discord import Message
from emoji import emoji_list

from bot.db.utils import Entity, Mapper, Id, Crud, inject_conn, DBConnection



@dataclass
class MessageEmojiEntity(Entity):
    __table_name__ = "server.message_emoji"

    message_id: Id
    emoji_id: Id
    count: int



class MessageEmojiMapper(Mapper[Message, Tuple[MessageEmojiEntity, ...]]):
    async def map(self, obj: Message) -> Tuple[MessageEmojiEntity, ...]:
        message = obj

        unicode_emojis = Counter([item['emoji'] for item in emoji_list(message.content)])
        discord_emojis = Counter(re.findall(r"<a?:\d+:\w+>", message.content))

        return (MessageEmojiEntity(message.id, message.id, 0),)



class MessageEmojiRepository(Crud[MessageEmojiEntity]):
    def __init__(self) -> None:
        super().__init__(entity=MessageEmojiEntity)


    @inject_conn
    async def insert(self, conn: DBConnection, data: MessageEmojiEntity) -> None:
        await conn.execute(f"""
            INSERT INTO server.message_emoji AS a (message_id, emoji_id, count)
            VALUES ($1, $2, $3)
            ON CONFLICT (message_id, emoji_id) DO UPDATE
                SET count = count + $3
        """, data.message_id, data.emoji_id, data.count)


    @inject_conn
    async def soft_delete(self, conn: DBConnection, id: Id) -> None:
        # TODO: soft_delete not implemented
        raise NotImplemented
