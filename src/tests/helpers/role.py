from unittest.mock import MagicMock

import discord

from role.model import Role

__all__ = ['create_discord_role', 'create_db_role']

DEFAULTS = {
    'discord_id': '00123456',
    'name': 'role name',
    'color': 0xFF0000
}


def create_discord_role(
        *,
        id: str = DEFAULTS['discord_id'],
        name: str = DEFAULTS['name'],
        color: str = hex(DEFAULTS['color'])
):
    role = MagicMock(spec=discord.Role)
    role.id = id
    role.name = name
    role.color = discord.Color.from_str(color)
    return role


def create_db_role(
        *,
        id: str = None,
        discord_id: str = DEFAULTS['discord_id'],
        name: str = DEFAULTS['name'],
        color: int = DEFAULTS['color']
):
    role = Role()
    role.id = id
    role.discord_id = discord_id
    role.name = name
    role.color = color
    return role
