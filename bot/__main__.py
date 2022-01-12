import logging
import os
import time

import discord
import redis
from discord.ext import commands
from dotenv import load_dotenv

from bot.bot import MasarykBOT
from bot.cogs.utils.db import Database
from bot.cogs.utils.logging import setup_logging

initail_cogs = [
    "bot.cogs.verification",
    "bot.cogs.cog_manager",
    "bot.cogs.leaderboard",
    "bot.cogs.starboard",
    "bot.cogs.bookmark",
    "bot.cogs.rolemenu",
    "bot.cogs.seasonal",
    "bot.cogs.subject",
    "bot.cogs.errors",
    "bot.cogs.logger",
    "bot.cogs.markov",
    "bot.cogs.rules",
    "bot.cogs.admin",
    "bot.cogs.eval",
    "bot.cogs.help",
    "bot.cogs.info",
    "bot.cogs.fun"
]

if __name__ == "__main__":
    load_dotenv()
    setup_logging()

    log = logging.getLogger()

    if os.getenv("POSTGRES") is None:
        log.exception("postgresql connection is required to run the bot, exiting...")
        exit(1)

    if os.getenv("TOKEN") is None:
        log.exception("discord bot token is required to run the bot, exiting...")
        exit(1)

    redis_client = None
    if os.getenv("REDIS"):
        while True:
            try:
                host, port = os.getenv("REDIS").split(":")
                redis_client = redis.Redis(host=host, port=port, db=0,
                                        decode_responses=True)
                redis_client.get("--test--")
                break
            except redis.exceptions.BusyLoadingError:
                log.warning("redis is loading, sleeping for 10 seconds...")
                time.sleep(10)
            except redis.exceptions.ConnectionError:
                log.exception("redis connection failed, exiting...")
                exit(1)


    intents = discord.Intents(
        guilds=True,
        guild_messages=True,
        members=True,
        presences = True,
        emojis=True,
        guild_reactions=True,
        dm_reactions=True)

    bot = MasarykBOT(db=Database.connect(os.getenv("POSTGRES")),
                     redis=redis_client,
                     command_prefix=commands.when_mentioned_or("!"),
                     intents=intents,
                     allowed_mentions=discord.AllowedMentions(roles=False, everyone=False, users=True),)

    for extension in initail_cogs:
        try:
            bot.load_extension(extension)
        except Exception:
            log.error('Failed to load extension %s.', extension, exc_info=True)

    bot.run(os.getenv("TOKEN"), reconnect=True)
