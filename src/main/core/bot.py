import logging
from typing import Any, Type, cast

import discord
from discord.ext import commands

__all__ = ['MasarykBot']

from core.context import Context

log = logging.getLogger(__name__)

intents = discord.Intents(
    guilds=True,
    guild_messages=True,
    members=True,
    presences=True,
    emojis=True,
    guild_reactions=True,
    dm_reactions=True,
    message_content=True
)


class MasarykBot(commands.Bot):
    def __init__(self, command_prefix: str = '!'):
        super().__init__(command_prefix, intents=intents)

    @staticmethod
    async def on_ready() -> None:
        log.info("bot is ready")

    async def add_cog(self, cog: commands.Cog, *args: Any, **kwargs: Any) -> None:
        log.info("loading cog: %s", cog.qualified_name)
        return await super().add_cog(cog, *args, **kwargs)

    async def get_context(self, origin: discord.Message | discord.Interaction, /, *,
                          cls: Type[commands._types.ContextT] = discord.utils.MISSING) -> Any:
        """
        Provides all commands with our custom context, instead of the default commands.Context
        """

        cls = cast(Type[commands._types.ContextT], Context) if cls is discord.utils.MISSING else cls
        return await super().get_context(origin, cls=cls)
