from dataclasses import dataclass
import re
from typing import Tuple

from discord import Message
from discord.ext import commands

import inject
from emoji import emoji_list

from __oild.bot.db.utils import Entity, Mapper, Id, Crud, inject_conn, DBConnection
from src.bot import Context, get_emoji_id, convert_emoji, MessageEmote


@dataclass
class MessageEmojiEntity(Entity):
    __table_name__ = "server.message_emoji"

    message_id: Id
    emoji_id: Id
    count: int


class MessageEmojiMapper(Mapper[MessageEmote, Tuple[MessageEmojiEntity, ...]]):
    @inject.autoparams('bot')
    async def map(self, obj: MessageEmote, bot: commands.Bot) -> MessageEmojiEntity:
        message, emoji = obj.message, obj.emoji
        return MessageEmojiEntity(message.id, get_emoji_id(emoji), 1)

    @staticmethod
    async def map_emojis(bot: commands.Bot, obj: Message) -> Tuple[MessageEmote, ...]:
        message = obj
        ctx = await bot.get_context(message, cls=Context)

        unicode_emojis = [item['emoji'] for item in emoji_list(message.content)]
        discord_emojis = [await convert_emoji(ctx, emoji) for emoji in re.findall(r"<a?:\w+:\d+>", message.content)]

        return tuple(MessageEmote(message, emoji) for emoji in unicode_emojis + discord_emojis)


class MessageEmojiRepository(Crud[MessageEmojiEntity]):
    def __init__(self) -> None:
        super().__init__(entity=MessageEmojiEntity)

    @inject_conn
    async def insert(self, conn: DBConnection, data: MessageEmojiEntity) -> None:
        await conn.execute(f"""
            INSERT INTO server.message_emoji AS em (message_id, emoji_id, count)
            VALUES ($1, $2, $3)
            ON CONFLICT (message_id, emoji_id) DO UPDATE
                SET count = em.count + $3
        """, data.message_id, data.emoji_id, data.count)

    @inject_conn
    async def soft_delete(self, conn: DBConnection, id: Id) -> None:
        # TODO: soft_delete not implemented
        raise NotImplemented
