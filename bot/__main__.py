import asyncio
import logging
import os
from typing import Optional

import asyncpg
import discord
import inject
import aioredis
from discord.ext import commands
from dotenv import load_dotenv

from bot.bot import MasarykBOT
from bot.cogs.utils.logging import setup_logging
from bot.db.messages import MessageDao
from bot.db.utils import Pool, Url



initail_cogs = [
    "bot.cogs.markov",
]

intents = discord.Intents(
        guilds=True,
        guild_messages=True,
        members=True,
        presences = True,
        emojis=True,
        guild_reactions=True,
        dm_reactions=True,
        message_content=True
)
bot = MasarykBOT(
    command_prefix=commands.when_mentioned_or("!"),
    intents=intents,
    allowed_mentions=discord.AllowedMentions(
        roles=False,
        everyone=False,
        users=True
    ),
)

log = logging.getLogger()


async def connect_db(url: Url) -> Pool:
    pool = None
    while pool is None:
        pool = await asyncpg.create_pool(postgres_url, command_timeout=1280)
    return pool



def connect_redis(url: Url) -> aioredis.Redis:
    return aioredis.from_url(url, decode_responses=True)



def setup_injections(db_pool: Optional[Pool], redis: Optional[aioredis.Redis]):
    def inner(binder: inject.Binder) -> None:
        binder.bind(Pool, db_pool)
        binder.bind(MessageDao, MessageDao())
        binder.bind(aioredis.Redis, redis)
    return inner



async def load_extensions() -> None:
    for extension in initail_cogs:
        try:
            await bot.load_extension(extension)
        except Exception:
            log.error('Failed to load extension %s.', extension, exc_info=True)



async def main() -> None:
    if (token := os.getenv("TOKEN")) is None:
        log.exception("discord bot token is required to run the bot, exiting...")
        exit(1)

    async with bot:
        await load_extensions()
        await bot.start(token, reconnect=True)



if __name__ == "__main__":
    load_dotenv()
    setup_logging()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    pool = None
    if postgres_url := os.getenv("POSTGRES"):
        pool = loop.run_until_complete(connect_db(postgres_url))

    redis = None
    if redis_url := os.getenv("REDIS"):
        redis = connect_redis(redis_url)

    inject.configure()
    inject.configure_once(setup_injections(pool, redis))
    asyncio.run(main())
