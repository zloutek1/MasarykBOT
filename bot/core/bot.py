import asyncio
import sys
import time
import logging

import discord
from discord import Color, Embed, Game
from discord.ext.commands import Bot

import traceback
import datetime
import json

from core.utils import context, db
from core.utils.db import Database


class LoggingHandler(logging.StreamHandler):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(self)

        self.temp = ""

    def emit(self, record):
        msg = self.format(record)

        if len(self.temp) + len(msg) < 1900:
            self.temp += f"{msg}\n"
            return

        with open("assets/local_db.json", "r", encoding="utf-8") as file:
            local_db = json.load(file)
            for channel_id in local_db["log_channels"]:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    self.bot.loop.create_task(channel.send(f"`{self.temp}`"))


class MasarykBot(Bot):
    def __init__(self, *args, activity=Game(name="Commands: !help"), **kwargs):
        super().__init__(*args, **kwargs)

        self.ininial_params = args, kwargs
        self.default_activity = activity

        self.setup_logging()
        self.loop.create_task(self.handle_database())

        self.readyCogs = {}

    """--------------------------------------------------------------------------------------------------------------------------"""

    def setup_logging(self):
        log = logging.getLogger()
        log.setLevel(logging.INFO)

        dt_fmt = '%Y-%m-%d %H:%M:%S'
        fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')

        handler = logging.FileHandler(filename='assets/masaryk.log', encoding='utf-8', mode='w')
        handler.setFormatter(fmt)
        log.addHandler(handler)

        # handler = LoggingHandler(bot=self)
        # handler.setFormatter(fmt)
        # log.addHandler(handler)

        self.log = log

    """--------------------------------------------------------------------------------------------------------------------------"""

    async def handle_database(self):
        await self.wait_until_ready()
        attempts = 0

        while True:
            try:
                self.db = await Database.connect()

                print("\n    [BOT] Database online: connected.\n")

                await self.change_presence(status=discord.Status.online, activity=self.default_activity)

                await self.trigger_event("on_ready")
                await self.bot_ready()

                break

            except db.DatabaseConnectionError as e:
                self.db = Database()

                dots = ("." * (attempts % 3 + 1) + "   ")[:3]
                self.log.error(e)
                print("\r    [BOT] Database offline: reconnecting" + dots, end="")

                await self.change_presence(status=discord.Status.dnd, activity=Game(name="Database offline"))

                await asyncio.sleep(2)
                attempts += 1

    async def process_commands(self, message):
        # send custom Context instead of the discord API's Context
        ctx = await self.get_context(message, cls=context.Context)

        if ctx.command is None:
            return

        await self.invoke(ctx)

    """--------------------------------------------------------------------------------------------------------------------------"""

    def handle_exit(self):
        # finish runnings tasks and logout bot

        self.loop.run_until_complete(self.logout())
        for task in asyncio.Task.all_tasks(loop=self.loop):
            if task.done():
                task.exception()
                continue

            task.cancel()

            try:
                self.loop.run_until_complete(asyncio.wait_for(task, 5, loop=self.loop))
                task.exception()
            except asyncio.InvalidStateError:
                pass
            except asyncio.TimeoutError:
                pass
            except asyncio.CancelledError:
                pass

        if self.db and self.db.pool:
            self.db.pool.close()
            self.loop.run_until_complete(self.db.pool.wait_closed())

    """--------------------------------------------------------------------------------------------------------------------------"""

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

    """--------------------------------------------------------------------------------------------------------------------------"""

    async def bot_ready(self):
        await self.wait_until_ready()

        while True:
            await asyncio.sleep(1)
            if all(self.readyCogs.values()) or len(self.readyCogs.values()) == 0:
                break

        self.intorduce()

    """--------------------------------------------------------------------------------------------------------------------------"""

    def intorduce(self):
        bot_name = self.user.name.encode(errors='replace').decode()

        print("\n\n\n")
        print("""               .,***,.
        /.             *%&*
     #%     /%&&&%            %#
    &   *&&&&&*%     /&&/     &/
   %*  &&&&&&& #&&%         (&&&%&,
   /( %&&&&&&& /(*            .&&&%
    ,%%&&         ....       .&%
      %& *%&&&&&&&&&&&&&&,  ,(.
      (&&&&&&&&&&&&&&%&&&&.   &&
       /&%&%,.*&%&%%&     *&  %&
        %&  ,%. .&,&. *&&  #*
        %&  ,%. .& .&.    (&   (
        (%&(   %&(   *%&&%     &
         &&%  (&  *%(       ,&
          &&&&&% ,&&(  .&   (
          ,&   .**.    ,&   *
           &%*#&&&%.. %&&&(
           /&&&&&/           %
             &&      /  (%&&(
              %% %   #&&&&.
               *&&, ,&&,
                 /&&&.                 \n""")
        print("     [BOT] {0} ready to serve! \n\n\n".format(bot_name))

    """--------------------------------------------------------------------------------------------------------------------------"""

    async def trigger_event(self, event_name, *args, **kwargs):
        events = []
        for cog_name, cog in self.cogs.items():
            event = list(
                map(lambda event: event[1],
                    filter(lambda listener: listener[0] == event_name,
                           cog.get_listeners()))
            )

            events += event

        if hasattr(self, event_name):
            events.append(getattr(self, event_name))

        tasks = []
        for event in events:
            task = self.loop.create_task(event(*args, **kwargs))
            tasks.append(task)

        await asyncio.wait(tasks)

    """--------------------------------------------------------------------------------------------------------------------------"""

    async def on_error(self, event, *args, **kwargs):
        exc_type, exc_value, exc_traceback = sys.exc_info()

        exc = traceback.format_exception(exc_type, exc_value, exc_traceback, chain=False)

        description = '```py\n%s\n```' % ''.join(exc)
        time = datetime.datetime.utcnow()

        message = 'Event {0} at {1}: More info: {2}'.format(event, time, description)
        embed = Embed(
            title='Event {0} at {1}:'.format(event, time),
            description=description[-1500:],
            color=Color.red()
        )

        with open("assets/local_db.json", "r", encoding="utf-8") as file:
            local_db = json.load(file)
            for channel_id in local_db["error_channels"]:
                channel = self.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)

        print(message)
