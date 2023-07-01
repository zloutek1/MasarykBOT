from dataclasses import dataclass

import discord
from discord.ext import commands

from __oild.bot.utils.context import Context

AnyEmote = discord.Emoji | discord.PartialEmoji | str


@dataclass(frozen=True)
class MessageEmote:
    message: discord.Message
    emoji: AnyEmote


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
    except commands.BadArgument:
        pass

    try:
        return await commands.PartialEmojiConverter().convert(ctx, emoji)
    except commands.BadArgument:
        pass

    return emoji
