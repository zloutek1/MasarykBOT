from unittest.mock import MagicMock

import discord


def create_guild(name: str):
    guild = MagicMock(spec=discord.Guild)
    guild.id = "770041446911123456"
    guild.name = name
    guild.icon = _create_icon("https://google.com")
    return guild


def _create_icon(url: str):
    icon = MagicMock(spec=discord.Attachment)
    icon.url = url
    return icon


def create_role(name: str):
    role = MagicMock(spec=discord.Role)
    role.id = "770041446911123456"
    role.name = name
    role.color = discord.Color.from_str("0xFF00FF")
    return role


def create_icon(url: str):
    pass
