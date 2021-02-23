import os
import logging
import traceback

import discord
from discord.ext import commands
from dotenv import load_dotenv

from bot.bot import MasarykBOT
from bot.cogs.utils.logging import setup_logging
from bot.cogs.utils.db import Database


initail_cogs = [
    "bot.cogs.verification",
    "bot.cogs.cog_manager",
    "bot.cogs.leaderboard",
    "bot.cogs.starboard",
    "bot.cogs.rolemenu",
    "bot.cogs.subject",
    "bot.cogs.errors",
    "bot.cogs.logger",
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
        exit()

    if os.getenv("TOKEN") is None:
        log.exception("discord bot token is required to run the bot, exiting...")
        exit()

    intents = discord.Intents(
        guilds=True,
        guild_messages=True,
        members=True,
        presences = True,
        emojis=True,
        guild_reactions=True)

    bot = MasarykBOT(command_prefix=commands.when_mentioned_or("!"),
                     intents=intents,
                     allowed_mentions=discord.AllowedMentions(roles=False, everyone=False, users=True),)

    bot.db = Database.connect(os.getenv("POSTGRES"))

    for extension in initail_cogs:
        try:
            bot.load_extension(extension)
        except Exception:
            log.error('Failed to load extension %s.', extension)
            traceback.print_exc()

    bot.run(os.getenv("TOKEN"), reconnect=True)
