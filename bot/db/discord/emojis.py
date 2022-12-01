from dataclasses import dataclass, astuple
from datetime import datetime
from typing import Optional

from discord import Emoji, PartialEmoji
from emoji import demojize

from bot.db.utils import Crud, DBConnection, Id, Mapper, Url, inject_conn, Entity
from bot.utils import AnyEmote
from bot.utils.emoji import get_emoji_id



@dataclass
class EmojiEntity(Entity):
    id: Id
    name: str
    url: Url
    animated: bool
    created_at: datetime
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None



class EmojiMapper(Mapper[AnyEmote, EmojiEntity]):
    async def map(self, obj: AnyEmote) -> EmojiEntity:
        if isinstance(obj, str):
            return self._map_unicode(obj)
        else:
            return self._map_discord(obj)


    @staticmethod
    def _map_unicode(emoji: str) -> EmojiEntity:
        emoji_id = get_emoji_id(emoji)
        hex_id = '_'.join(hex(ord(char))[2:] for char in emoji)
        url = "https://unicode.org/emoji/charts/full-emoji-list.html#{hex}".format(hex=hex_id)
        return EmojiEntity(emoji_id, demojize(emoji).strip(':'), url, False)


    @staticmethod
    def _map_discord(emoji: Emoji | PartialEmoji) -> EmojiEntity:
        return EmojiEntity(get_emoji_id(emoji), emoji.name, str(emoji.url), emoji.animated, emoji.created_at)



class EmojiRepository(Crud[EmojiEntity]):
    def __init__(self) -> None:
        super().__init__(entity=EmojiEntity)


    @inject_conn
    async def insert(self, conn: DBConnection, data: EmojiEntity) -> None:
        await conn.execute(f"""
            INSERT INTO server.emojis AS e (id, name, url, animated)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE
                SET name=$2,
                    url=$3,
                    animated=$4,
                    edited_at=NOW()
                WHERE e.name<>excluded.name OR
                      e.url<>excluded.url OR
                      e.animated<>excluded.animated
        """, astuple(data))
