import os
import asyncio
import asyncpg
import logging

from bot import MasarykBOT
from cogs.utils.logging import setup_logging

from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    setup_logging()

    loop = asyncio.get_event_loop()
    log = logging.getLogger()

    try:
        pool = loop.run_until_complete(asyncpg.create_pool(os.getenv("POSTGRES"), command_timeout=60))
    except Exception:
        log.exception('Could not set up PostgreSQL. Exiting.')
        exit()

    bot = MasarykBOT(command_prefix="!")
    bot.pool = pool
    bot.run(os.getenv("TOKEN"))

