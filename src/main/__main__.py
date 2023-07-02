import asyncio
import os

from dependency_injector.wiring import Provide, inject, register_loader_containers
from dotenv import load_dotenv

from core.bot import MasarykBot
from core.database import Database
from core.inject import Inject


@inject
async def migrate_db(db: Database = Provide[Inject.database]) -> None:
    await db.create_database()


@inject
async def main(cogs: list = Provide[Inject.cog.all]) -> None:
    await migrate_db()

    bot = MasarykBot()
    async with bot:
        for setup_cog in cogs:
            await setup_cog(bot)

        await bot.start(os.getenv("TOKEN"))


if __name__ == "__main__":
    load_dotenv()

    container = Inject()
    container.wire(modules=[__name__])
    register_loader_containers(container)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down")
