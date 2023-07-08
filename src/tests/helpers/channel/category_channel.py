from unittest.mock import MagicMock

import discord

from channel.category.model import CategoryChannel

__all__ = ['create_discord_category_channel', 'create_db_category_channel']


def create_discord_category_channel(
        *,
        id: str = "98765432101",
        name: str = "Category Channel name"
):
    categoroy_channel = MagicMock(spec=discord.CategoryChannel)
    categoroy_channel.id = id
    categoroy_channel.name = name
    categoroy_channel._type = discord.ChannelType.category
    return categoroy_channel


def create_db_category_channel(
        *,
        id: str | None = None,
        discord_id: str = "98765432101",
        name: str = "Category Channel name"
):
    category_channel = CategoryChannel()
    category_channel.id = id
    category_channel.discord_id = discord_id
    category_channel.name = name
    return category_channel
