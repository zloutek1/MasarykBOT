import re
import inject
from typing import List, Sequence, Tuple, Union
from emoji import demojize, get_emoji_regexp

from discord import Emoji, Message, PartialEmoji

from bot.db.tables import EMOJIS
from bot.db.utils import (Crud, DBConnection, Id, Mapper, Url, withConn)



AnyEmote = Union[Emoji, PartialEmoji, str]
Columns = Tuple[Id, str, Url, bool]



def emoji_hashcode(emoji: Union[Emoji, PartialEmoji, str]) -> int:
    if isinstance(emoji, str):
        return sum(map(ord, emoji))

    if emoji.id is None:
        raise AssertionError("Emoji has to have an id")
    return emoji.id



class EmojiMapper(Mapper[AnyEmote, Columns]):
    async def map(self, obj: AnyEmote) -> Columns:
        if isinstance(obj, str):
            return self._map_unicode(obj)
        else:
            return self._map_discord(obj)

    @staticmethod
    def _map_unicode(emoji: str) -> Columns:
        emoji_id = sum(map(ord, emoji))
        hex_id = '_'.join(hex(ord(char))[2:] for char in emoji)
        url = "https://unicode.org/emoji/charts/full-emoji-list.html#{hex}".format(hex=hex_id)
        return (emoji_id, demojize(emoji).strip(':'), url, False)

    @staticmethod
    def _map_discord(emoji: Emoji | PartialEmoji) -> Columns:
        if emoji.id is None:
            raise AssertionError("Emoji has to have an id")
        return (emoji.id, emoji.name, str(emoji.url), emoji.animated)



class MessageEmojiMapper(Mapper[Message, Sequence[Columns]]):
    emojiMapper = inject.attr(EmojiMapper)

    async def map(self, obj: Message) -> List[Columns]:
        regular = self._map_discord(obj, animatied=False)
        animated = self._map_discord(obj, animatied=True)
        unicode = await self._map_unicode(obj)
        return regular + animated + unicode

    
    def _map_discord(self, message: Message, animatied: bool) -> List[Columns]:
        regexp = r"<a:([\w~]+):(\d+)>" if animatied else r"<:([\w~]+):(\d+)>"
        return [(int(emoji_id), emoji_name, self.to_url(int(emoji_id), animated=animatied), animatied)
                for (emoji_name, emoji_id) in re.findall(regexp, message.content)]

    
    async def _map_unicode(self, message: Message) -> List[Columns]:
        emojis = get_emoji_regexp().findall(message.content)
        return [await self.emojiMapper.map(emoji) for emoji in emojis]


    @staticmethod
    def to_url(emoji_id: int, *, animated: bool=False) -> Url:
        return f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if animated else 'png'}"

    

class EmojiDao(Crud[Columns]):
    def __init__(self) -> None:
        super().__init__(table_name=EMOJIS)


    @withConn
    async def insert(self, conn: DBConnection, data: Sequence[Columns]) -> None:
        await conn.executemany(f"""
            INSERT INTO {EMOJIS} AS e (id, name, url, animated)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE
                SET name=$2,
                    url=$3,
                    animated=$4,
                    edited_at=NOW()
                WHERE e.name<>excluded.name OR
                      e.url<>excluded.url OR
                      e.animated<>excluded.animated
        """, data)