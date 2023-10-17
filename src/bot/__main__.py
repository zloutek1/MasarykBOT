import logging

import asyncio
import discord
from discord.ext import commands

from bot.bot import MasarykBOT

initial_cogs = [
    "bot.echo.echo_cog",
]


log = logging.getLogger(__name__)


TOKEN = "NTczNTg4MjAyMDcwNDc0ODAz.GkOMoh.3FlismwzY0nv9_Qveb0-fhUHXkVjpAoePoSQYM"

intents = discord.Intents.default()
intents.message_content = True

bot = MasarykBOT(
    command_prefix='!', 
    intents=intents
)

async def load_extensions():
    for extension in initial_cogs:
        try:
            await bot.load_extension(extension)
        except Exception as ex:
            log.error('Failed to load extension %s.', extension, exc_info=True)


async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

asyncio.run(main())