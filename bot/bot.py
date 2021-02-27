import asyncio
import logging
import traceback
from datetime import datetime, timezone
from collections import Counter

from typing import Optional

from discord.ext import commands

from bot.constants import Config
from bot.cogs.utils import context, db

DESCRIPTION = """
$ Hello
"""

log = logging.getLogger(__name__)


class MasarykBOT(commands.Bot):
    def __init__(self, database: db.Database, *args, description=DESCRIPTION, **kwargs):
        super().__init__(*args, **kwargs)

        self.db = database
        self.uptime: Optional[datetime] = None

    async def on_ready(self):
        if self.uptime is None:
            self.uptime = datetime.utcnow()

        log.info("Bot is now all ready to go")
        self.intorduce()

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=context.Context)

        if ctx.command is None:
            return

        log.info("user %s used command: %s", message.author, message.content)
        try:
            await self.invoke(ctx)
        except KeyboardInterrupt:
            log.info("User initiated power off, closing")
            await self.close()

    async def on_message(self, message):
        if message.author.bot:
            return
        if Config.bot.DEBUG and not message.author.guild_permissions.administrator:
            return
        await self.process_commands(message)

    def add_cog(self, cog: commands.Cog) -> None:
        log.info("loading cog: %s", cog.qualified_name)
        super().add_cog(cog)

    def remove_cog(self, name: str) -> None:
        log.info("unloading cog: %s", name)
        super().remove_cog(name)

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
