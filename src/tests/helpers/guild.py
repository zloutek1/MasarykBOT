from unittest.mock import MagicMock

import discord

from guild.model import Guild
from helpers.attachment import create_attachment
from role.model import Role

__all__ = ['create_discord_guild']


def create_discord_guild(
        *,
        id: str = "98765432101",
        name: str = "Guild name",
        icon_url: str = "https://google.com",
        roles: list[discord.Role] = None
):
    guild = MagicMock(spec=discord.Guild)
    guild.id = id
    guild.name = name
    guild.icon = create_attachment(url=icon_url)
    guild.roles = roles if roles else []
    return guild


def create_db_guild(
        *,
        id: str | None = None,
        discord_id: str = "98765432101",
        name: str = "Guild name",
        icon_url: str = "https://google.com",
        roles: list[Role] = None
):
    guild = Guild()
    guild.id = id
    guild.discord_id = discord_id
    guild.name = name
    guild.icon_url = icon_url
    guild.roles = roles if roles else []
    return guild
