import os
import asyncio
import logging
import traceback

from bot.bot import MasarykBOT
from bot.cogs.utils.logging import setup_logging
from bot.cogs.utils.db import Database

from dotenv import load_dotenv

initail_cogs = [
    "bot.cogs.verification",
    "bot.cogs.leaderboard",
    "bot.cogs.cog_manager",
    "bot.cogs.rolemenu",
    "bot.cogs.subject",
    "bot.cogs.logger",
    "bot.cogs.rules",
    "bot.cogs.eval",
    "bot.cogs.help",
    "bot.cogs.tags",
    "bot.cogs.info"
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

    bot = MasarykBOT(command_prefix="!")
    bot.db = Database.connect(os.getenv("POSTGRES"))

    for extension in initail_cogs:
        try:
            bot.load_extension(extension)
        except Exception:
            log.error(f'Failed to load extension {extension}.')
            traceback.print_exc()

    bot.run(os.getenv("TOKEN"))
