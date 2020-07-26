import os
import asyncio
import asyncpg
import logging
import traceback

from bot.bot import MasarykBOT
from bot.cogs.utils.logging import setup_logging

from dotenv import load_dotenv

initail_cogs = [
    "bot.cogs.verification",
    "bot.cogs.cog_manager",
    "bot.cogs.leaderboard",
    "bot.cogs.logger",
    "bot.cogs.rules",
    "bot.cogs.help",
    "bot.cogs.info"
]

if __name__ == "__main__":
    load_dotenv()
    setup_logging()

    loop = asyncio.get_event_loop()
    log = logging.getLogger()

    if os.getenv("POSTGRES") is None:
        log.exception("postgresql connection is required to run the bot, exiting...")
        exit()

    if os.getenv("TOKEN") is None:
        log.exception("discord bot token is required to run the bot, exiting...")
        exit()

    try:
        pool = loop.run_until_complete(asyncpg.create_pool(os.getenv("POSTGRES"), command_timeout=60))
    except Exception:
        log.exception('Could not set up PostgreSQL. Exiting.')
        exit()

    bot = MasarykBOT(command_prefix="!")
    bot.pool = pool

    for extension in initail_cogs:
        try:
            bot.load_extension(extension)
        except Exception:
            log.error(f'Failed to load extension {extension}.')
            traceback.print_exc()

    bot.run(os.getenv("TOKEN"))
