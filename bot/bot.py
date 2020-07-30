import discord
from discord.ext import commands

import asyncio
import logging
import traceback
from datetime import datetime, timezone
from collections import Counter

from bot.cogs.utils import context

description = """
$ Hello
"""

log = logging.getLogger(__name__)


class MasarykBOT(commands.Bot):
    def __init__(self, *args, description=description, **kwargs):
        super().__init__(*args, **kwargs)

        self.spam_control = commands.CooldownMapping.from_cooldown(10, 12.0, commands.BucketType.user)
        self._auto_spam_count = Counter()

        self.db = None

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = datetime.utcnow()

        self.intorduce()

    async def on_command_error(self, ctx, error):
        red = discord.Color.red()

        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send_embed('This command cannot be used in private messages.', color=red)

        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send_embed('Sorry. This command is disabled and cannot be used.', color=red)

        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                log.error(f'In {ctx.command.qualified_name}:')
                traceback.print_tb(original.__traceback__)
                log.error(f'{original.__class__.__name__}: {original}')

        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send_embed(error, color=red)

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send_embed("Sorry. You don't have permissions to use this command", color=red)

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=context.Context)

        if ctx.command is None:
            return

        bucket = self.spam_control.get_bucket(message)
        current = message.created_at.replace(tzinfo=timezone.utc).timestamp()
        retry_after = bucket.update_rate_limit(current)
        author_id = message.author.id
        if retry_after:
            self._auto_spam_count[author_id] += 1
            if self._auto_spam_count[author_id] >= 5:

                # # HERE HANDLE BLACKLISTING OF SPAMMERS
                print("blacklisting", author_id)
                # # HERE HANDLE BLACKLISTING OF SPAMMERS

                del self._auto_spam_count[author_id]
            return
        else:
            self._auto_spam_count.pop(author_id, None)

        log.info(f"user {message.author} used command: {message.content}")
        await self.invoke(ctx)

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

    def add_cog(self, cog: commands.Cog) -> None:
        super().add_cog(cog)
        log.info(f"Cog loaded: {cog.qualified_name}")

    def remove_cog(self, name: str) -> None:
        super().remove_cog(name)
        log.info(f"Cog unloaded: {name}")

    def run(self, token):
        try:
            super().run(token, reconnect=True)
        finally:
            for task in asyncio.Task.all_tasks(loop=self.loop):
                task.cancel()
            log.info("exiting, bye")

    def intorduce(self):
        bot_name = self.user.name.encode(errors='replace').decode()

        log.info("Bot is now all ready to go")
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
