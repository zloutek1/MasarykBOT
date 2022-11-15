import asyncio
import logging
import os
from typing import Callable, Optional

import asyncpg
import discord
import inject
import aioredis
from discord.ext import commands
from dotenv import load_dotenv

from bot.bot import MasarykBOT
from bot.cogs.utils.logging import setup_logging
from bot.db import connect_db, setup_injections as setup_db_injections
from bot.db.utils import Pool, Url


# TODO: implement Seasonal
# TODO: implement LaTeX
initail_cogs = [
    "bot.cogs.admin",
    "bot.cogs.auto_thread",
    "bot.cogs.bookmark",
    "bot.cogs.cog_manager",
    "bot.cogs.errors",
    "bot.cogs.eval",
    "bot.cogs.fun",
    "bot.cogs.help",
    "bot.cogs.info",
    "bot.cogs.markov",
    "bot.cogs.leaderboard",
    "bot.cogs.rolemenu",
    "bot.cogs.rules",
    "bot.cogs.starboard",
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



async def connect_redis(url: Url) -> aioredis.Redis:
    redis: aioredis.Redis = aioredis.from_url(url, decode_responses=True)
    await redis.set('ping', 'pong')
    assert 'pong' == await redis.get('ping')
    return redis



def setup_injections(db_pool: Optional[Pool], redis: Optional[aioredis.Redis]) -> Callable[..., None]:
    def inner(binder: inject.Binder) -> None:
        if db_pool:
            binder.bind(Pool, db_pool)
        
        if redis:
            binder.bind(aioredis.Redis, redis)

        binder.install(setup_db_injections)
    return inner



async def load_extensions() -> None:
    for extension in initail_cogs:
        try:
            await bot.load_extension(extension)
        except Exception:
            log.error('Failed to load extension %s.', extension, exc_info=True)



async def main() -> None:
    if not (token := os.getenv("TOKEN")):
        log.exception("discord bot token is required to run the bot, exiting...")
        exit(1)

    pool = None
    if (postgres_url := os.getenv("POSTGRES")):
        pool = await connect_db(postgres_url)

    redis = None
    if redis_url := os.getenv("REDIS"):
        redis = await connect_redis(redis_url)
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: 
        inject.configure_once(setup_injections(pool, redis))
    )

    async with bot:
        await load_extensions()
        await bot.start(token, reconnect=True)



if __name__ == "__main__":
    load_dotenv()
    setup_logging()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("exiting")
