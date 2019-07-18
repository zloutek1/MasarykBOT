import asyncio
import sys
import time

from discord.ext.commands import Bot

from core.utils import context, db
from core.utils.db import Database


class MasarykBot(Bot):
    def __init__(self, *args, db_config={}, **kwargs):
        super().__init__(*args, **kwargs)

        self.ininial_params = args, kwargs
        self.errors = []

        self.handle_database_connection(**db_config)

    def handle_database_connection(self, **db_config):
        ##
        # Connect to the database and try to reconnect every 2 minutes on fail
        ##
        while True:
            try:
                self.db = Database.connect(**db_config)
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
