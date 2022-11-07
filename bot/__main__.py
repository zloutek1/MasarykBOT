import asyncio
import logging
import os
import time
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
        dm_reactions=True
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


def connect_db(url: Optional[Url]) -> Optional[Pool]:
    if url is None:
        return None
    
    pool = None
    loop = asyncio.get_event_loop()
    
    try:
        while pool is None:
            pool = loop.run_until_complete(asyncpg.create_pool(url, command_timeout=1280))
            log.error("Failed to connect to database, reconnecting in 5 seconds...")
            time.sleep(5)

    except (OSError, TimeoutError):
        import re
        redacted_url = re.sub(r'\:(?!\/\/)[^\@]+', ":******", url)
        log.error("Failed to connect to database (%s)", redacted_url)
        return None
    
    log.info("Connected to database successfully")
    return pool



def connect_redis(url: Optional[Url]) -> Optional[aioredis.Redis]:
    if url is None:
        return None
    return aioredis.from_url(url, decode_responses=True)
    


def close_redis() -> None:
    redis = inject.instance(aioredis.Redis)
    if not redis:
        return
    asyncio.run(redis.close())



def setup_injections(binder: inject.Binder) -> None:
    postgres_url = os.getenv("POSTGRES")
    binder.bind(Pool, connect_db(postgres_url))
    binder.bind(MessageDao, MessageDao())

    redis_url = os.getenv("REDIS")
    binder.bind(aioredis.Redis, connect_redis(redis_url))



async def load_extensions():
    for extension in initail_cogs:
        try:
            await bot.load_extension(extension)
        except Exception:
            log.error('Failed to load extension %s.', extension, exc_info=True)


async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.getenv("TOKEN"), reconnect=True)


if __name__ == "__main__":
    load_dotenv()
    setup_logging()

    log = logging.getLogger()

    if os.getenv("TOKEN") is None:
        log.exception("discord bot token is required to run the bot, exiting...")
        exit(1)

    inject.configure_once(setup_injections)

    asyncio.run(main())
