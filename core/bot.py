import asyncio
import sys
import time

import discord
from discord import Color, Embed
from discord.ext.commands import Bot

import traceback
import datetime
import json

from core.utils import context, db
from core.utils.db import Database


class MasarykBot(Bot):
    def __init__(self, *args, db_config={}, **kwargs):
        super().__init__(*args, **kwargs)

        self.ininial_params = args, kwargs

        self.db_config = db_config
        self.loop.create_task(self.handle_database_connection())
        self.readyCogs = {}

        self.loop.create_task(self.bot_ready())

    async def handle_database_connection(self):
        attempts = 0
        reconnected = False
        while True:
            try:
                self.db = Database(self.db_config)
                print("\n    [BOT] Database online: connected.\n")

                if reconnected:
                    await self.trigger_event("on_ready")

                break

            except db.DatabaseConnectionError as e:
                self.db = Database()
                dots = ("." * (attempts % 3 + 1) + "   ")[:3]
                print("\r    [BOT] Database offline: reconnecting" + dots, end="")
                await asyncio.sleep(2)
                reconnected = True
                attempts += 1

    async def process_commands(self, message):
        # send custom Context instead of the discord API's Context
        ctx = await self.get_context(message, cls=context.Context)

        if ctx.command is None:
            return

        await self.invoke(ctx)

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

    async def bot_ready(self):
        await self.wait_until_ready()
        while True:
            await asyncio.sleep(1)
            if all(self.readyCogs.values()):
                break

        self.intorduce()

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

    async def trigger_event(self, event_name, *args, **kwargs):
        events = []
        for cog_name, cog in self.cogs.items():
            event = list(
                map(lambda event: event[1],
                    filter(lambda listener: listener[0] == event_name,
                           cog.get_listeners()))
            )

            events += event

        for event in events:
            await event(*args, **kwargs)

    async def on_error(self, event, *args, **kwargs):
        exc = traceback.format_exception(*sys.exc_info(), chain=False)

        description = '```py\n%s\n```' % ''.join(exc)
        time = datetime.datetime.utcnow()

        message = 'Event {0} at {1}: More info: {2}'.format(event, time, description)
        embed = Embed(
            title='Event {0} at {1}:'.format(event, time),
            description=description,
            color=Color.red()
        )

        with open("assets/local_db.json", "r", encoding="utf-8") as file:
            local_db = json.load(file)
            for channel_id in local_db["log_channels"]:
                channel = self.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)

        print(message)
