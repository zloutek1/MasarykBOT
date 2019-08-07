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

        self.loop.create_task(self.handle_database_connection(db_config))
        self.readyCogs = {}

        self.loop.create_task(self.bot_ready())

    async def handle_database_connection(self, db_config):
        while True:
            try:
                self.db = Database(db_config)
                print("[BOT] Database online: connected.")
                break

            except db.DatabaseConnectionError as e:
                self.db = Database()
                print("[BOT] Database offline: reconnecting.")
                await asyncio.sleep(10)

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
        print("     [BOT] {0.user.name} ready to serve! \n\n\n".format(self))
