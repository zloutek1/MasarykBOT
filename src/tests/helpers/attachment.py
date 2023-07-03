from unittest.mock import MagicMock

import discord

__all__ = ['create_attachment']


def create_attachment(
        *,
        id: str = "98765432103",
        url: str = "https://google.com"
):
    icon = MagicMock(spec=discord.Attachment)
    icon.id = id
    icon.url = url
    return icon
