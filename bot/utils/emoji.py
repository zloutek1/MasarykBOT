from typing import Optional

from bot.utils.context import Context
from .extra_types import AnyEmote
from discord.ext import commands



def get_emoji_id(emoji: AnyEmote) -> int:
    if isinstance(emoji, str):
        return sum(map(ord, emoji))
    assert emoji.id, f"emoji {emoji} has no id"
    return emoji.id


def get_emoji_name(emoji: AnyEmote) -> str:
    if isinstance(emoji, str):
        return emoji
    return emoji.name


async def convert_emoji(ctx: Context, emoji: str) -> AnyEmote:
    try:
        return await commands.EmojiConverter().convert(ctx, emoji)
    except Exception:
        pass

    try:
        return await commands.PartialEmojiConverter().convert(ctx, emoji)
    except Exception:
        pass
    
    return emoji