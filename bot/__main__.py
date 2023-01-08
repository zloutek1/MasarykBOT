import asyncio
import logging
import os
from typing import Callable, Optional

import discord
import inject
from discord.ext import commands
from discord.ext.commands import ExtensionFailed
from dotenv import load_dotenv

from bot.bot import MasarykBOT
from bot.cogs import setup_injections as setup_cog_injections
from bot.db import connect_db, Pool, setup_injections as setup_db_injections
from bot.utils import setup_logging, DatabaseRequiredException

# TODO: implement Seasonal
# TODO: implement LaTeX
# TODO: implement activity
initial_cogs = [
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
    "bot.cogs.role_menu",
    "bot.cogs.rules",
    "bot.cogs.starboard",
    "bot.cogs.logger",
    "bot.cogs.verification",
    "bot.cogs.course"
]

intents = discord.Intents(
    guilds=True,
    guild_messages=True,
    members=True,
    presences=True,
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


def setup_injections(db_pool: Optional[Pool], bot: commands.Bot) -> Callable[..., None]:
    def inner(binder: inject.Binder) -> None:
        binder.bind(commands.Bot, bot)
        if db_pool:
            binder.bind(Pool, db_pool)  # type: ignore[misc]
            binder.install(setup_db_injections)
            binder.install(setup_cog_injections)
    return inner


# noinspection PyBroadException
async def load_extensions() -> None:
    for extension in initial_cogs:
        try:
            await bot.load_extension(extension)
        except ExtensionFailed as ex:
            if isinstance(ex.__cause__, DatabaseRequiredException):
                log.warning('skipping extension %s [database required]', extension)
            else:
                log.error('Failed to load extension %s.', extension, exc_info=True)


async def main() -> None:
    if not (token := os.getenv("TOKEN")):
        log.exception("discord bot token is required to run the bot, exiting...")
        exit(1)

    pool: Optional[Pool] = None
    if postgres_url := os.getenv("POSTGRES"):
        pool = await connect_db(postgres_url)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: inject.configure_once(setup_injections(pool, bot)))

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
