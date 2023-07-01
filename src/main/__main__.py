import asyncio
import os

from dotenv import load_dotenv

from core.bot import MasarykBot
from core.inject import Inject


async def migrate_db() -> None:
    container = Inject()
    db = container.database()
    await db.create_database()


async def main() -> None:
    await migrate_db()

    bot = MasarykBot()
    await bot.load_extension("leaderboard")
    await bot.start(os.getenv("TOKEN"))


if __name__ == "__main__":
    load_dotenv()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down")
