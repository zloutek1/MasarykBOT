from typing import Union

import discord

from .context import Context


class GuildContext(Context):
    author: discord.Member
    guild: discord.Guild
    channel: Union[discord.VoiceChannel, discord.TextChannel, discord.Thread]
    me: discord.Member
    prefix: str


class GuildMessage(discord.Message):
    guild: discord.Guild



AnyEmote = discord.Emoji | discord.PartialEmoji | str
