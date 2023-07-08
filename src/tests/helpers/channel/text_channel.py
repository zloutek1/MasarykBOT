from unittest.mock import MagicMock

import discord

from channel.text.model import TextChannel

__all__ = ['create_discord_text_channel', 'create_db_text_channel']


def create_discord_text_channel(
        *,
        id: str = "98765432101",
        name: str = "Text Channel name"
):
    text_channel = MagicMock(spec=discord.TextChannel)
    text_channel.id = id
    text_channel.name = name
    text_channel._type = discord.ChannelType.text
    return text_channel


def create_db_text_channel(
        *,
        id: str | None = None,
        discord_id: str = "98765432101",
        name: str = "Text Channel name"
):
    text_channel = TextChannel()
    text_channel.id = id
    text_channel.discord_id = discord_id
    text_channel.name = name
    return text_channel
