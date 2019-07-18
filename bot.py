import asyncio
import sys
import time

from discord import Game
from discord.ext.commands import Bot, when_mentioned_or

from cogs.utils import context, db
from cogs.utils.db import Database
from config import BotConfig


class MasarykBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ininial_params = args, kwargs
        self.errors = []

        while True:
            try:
                self.db = Database.connect(**BotConfig.db_config)
                print("Database connected.")
                break
            except db.ConnectionError as e:
                print(f"{e}\nReconnecting to the database...")
                time.sleep(120)
            except KeyboardInterrupt:
                self.handle_exit()
                print("Bot shut down by KeyboardInterrupt")
                sys.exit(1)

    def handle_exit(self):
        # finish runnings tasks and logout bot

        self.loop.run_until_complete(self.logout())
        for t in asyncio.Task.all_tasks(loop=self.loop):
            if t.done():
                t.exception()
                continue
            t.cancel()
            try:
                self.loop.run_until_complete(asyncio.wait_for(t, 5, loop=self.loop))
                t.exception()
            except asyncio.InvalidStateError:
                pass
            except asyncio.TimeoutError:
                pass
            except asyncio.CancelledError:
                pass

    def start(self, *args, **kwargs):
        while True:
            try:
                # start the bot
                self.loop.run_until_complete(super().start(*args, **kwargs))
            except SystemExit:
                self.handle_exit()
            except KeyboardInterrupt:
                self.handle_exit()
                self.loop.close()
                print("Bot shut down by KeyboardInterrupt")
                break

            print("Bot restarting")
            super().__init__(*self.ininial_params[0], **self.ininial_params[1])

    async def process_commands(self, message):
        # send custom Context instead of the discord API's Context
        ctx = await self.get_context(message, cls=context.Context)

        if ctx.command is None:
            return

        await self.invoke(ctx)


bot = MasarykBot(
    command_prefix=when_mentioned_or(BotConfig.prefix),
    activity=Game(name="Commands: !help"),
    case_insensitive=True
)

# Internal/debug
bot.load_extension("cogs.events")
bot.load_extension("cogs.errors")

# Commands
bot.load_extension("cogs.picker")
bot.load_extension("cogs.antispam")


bot.start(BotConfig.token)
