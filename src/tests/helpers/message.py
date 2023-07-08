from unittest.mock import MagicMock

import discord

from message.model import Message

__all__ = ['create_discord_message', 'create_db_message']


def create_discord_message(
        *,
        id: str = "98765432101",
        content: str = "Hello World!"
):
    message = MagicMock(spec=discord.Message)
    message.id = id
    message.content = content
    return message


def create_db_message(
        *,
        id: str | None = None,
        discord_id: str = "98765432101",
        content: str = "Hello World!"
):
    message = Message()
    message.id = id
    message.discord_id = discord_id
    message.content = content
    return message
