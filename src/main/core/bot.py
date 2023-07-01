import discord
from discord.ext import commands

__all__ = ['MasarykBot']

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

    async def on_ready(self) -> None:
        print("bot is ready")
