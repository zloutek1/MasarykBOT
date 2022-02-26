import re
from datetime import datetime
from typing import List, Optional, Sequence, Tuple, Union, cast

from bot.db.utils import (Crud, DBConnection, FromMessageMapper, Id, Mapper,
                          Record, Table, Url, WrappedCallable, withConn)
from disnake import Emoji, Message, PartialEmoji
from emoji import demojize, get_emoji_regexp
from numpy import delete

AnyEmote = Union[Emoji, PartialEmoji, str]
Columns = Tuple[Id, str, Url, bool]

class EmojiDao(Table, Crud[Columns], Mapper[AnyEmote, Columns], FromMessageMapper[Columns]):
    HAS_EMOTE = r":[\w~]+:"
    REGULAR_REGEX = r"<:([\w~]+):(\d+)>"
    ANIMATED_REGEX = r"<a:([\w~]+):(\d+)>"

    @staticmethod
    async def prepare_one(emoji: AnyEmote) -> Columns:
        if isinstance(emoji, str):
            return await EmojiDao.prepare_unicode_emoji(emoji)

        assert emoji.id is not None, "Emoji has to have an id"
        return (emoji.id, emoji.name, str(emoji.url), emoji.animated)

    async def prepare(self, emojis: Sequence[AnyEmote]) -> List[Columns]:
        return [await self.prepare_one(emoji) for emoji in emojis]

    async def prepare_from_message(self, message: Message) -> List[Columns]:
        return (await self._prepare_from_message_content(message)
               + await self._prepare_from_message_reactions(message))

    @withConn
    async def select(self, conn: DBConnection, emoji_id: Id) -> List[Record]:
        return await conn.fetch("""
            SELECT * FROM server.emojis WHERE id=$1
        """, emoji_id)

    @withConn
    async def insert(self, conn: DBConnection, data: List[Columns]) -> None:
        await conn.executemany("""
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
        """, data)

    @withConn
    async def update(self, conn: DBConnection, data: List[Columns]) -> None:
        insert = cast(WrappedCallable, self.insert)
        await insert.__wrapped__(self, conn, data)

    @withConn
    async def soft_delete(self, conn: DBConnection, ids: List[Tuple[Id]]) -> None:
        await conn.executemany("""
            UPDATE server.emojis
            SET deleted_at=NOW()
            WHERE id = $1;
        """, ids)


    @staticmethod
    async def prepare_unicode_emoji(emoji: str) -> Columns:
        emoji_id = sum(map(ord, emoji))
        hex_id = '_'.join(hex(ord(char))[2:] for char in emoji)
        url = "https://unicode.org/emoji/charts/full-emoji-list.html#{hex}".format(hex=hex_id)
        return (emoji_id, demojize(emoji).strip(':'), url, False)


    @staticmethod
    def to_url(emoji_id: int, *, animated: bool=False) -> Url:
        return f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if animated else 'png'}"

    async def _prepare_emojis_from_message(self, message: Message, regex: str, *, is_animated: bool) -> List[Columns]:
        emojis = re.findall(regex, message.content)
        return [(int(emoji_id), emoji_name, self.to_url(int(emoji_id), animated=is_animated), is_animated)
                for (emoji_name, emoji_id) in emojis]

    async def _prepare_from_message_content(self, message: Message) -> List[Columns]:
        if not re.search(self.HAS_EMOTE, demojize(message.content)):
            return []

        regular_emojis = await self._prepare_emojis_from_message(message, self.REGULAR_REGEX, is_animated=False)
        animated_emojis = await self._prepare_emojis_from_message(message, self.ANIMATED_REGEX, is_animated=True)
        unicode_emojis = [await EmojiDao.prepare_unicode_emoji(emoji)
                          for emoji in get_emoji_regexp().findall(message.content)]

        return regular_emojis + animated_emojis + unicode_emojis

    async def _prepare_from_message_reactions(self, message: Message) -> List[Columns]:
        return [await self.prepare_one(reaction.emoji)
                for reaction in message.reactions]
