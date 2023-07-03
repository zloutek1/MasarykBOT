from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    pass


class Context(commands.Context["MasarykBot"]):
    """
    Provide custom methods in the context of commands.
    """

    async def send_error(self, title: str, body: str) -> discord.Message:
        embed = self._get_error_embed(title, body)
        return await self.send(embeds=[embed])

    @staticmethod
    def _get_error_embed(title: str, body: str) -> discord.Embed:
        """Return an embed that contains the exception."""
        return discord.Embed(
            title=title,
            colour=discord.Color.from_str("#F47174"),
            description=body
        )
