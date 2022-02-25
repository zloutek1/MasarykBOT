import logging
from datetime import datetime
from typing import Any, Optional, cast

from disnake import Message, User
from disnake.ext import commands

from bot.cogs.utils import context
from bot.constants import Config

log = logging.getLogger(__name__)


class MasarykBOT(commands.Bot):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)


    async def process_commands(self, message: Message) -> None:
        ctx = await self.get_context(message, cls=context.Context)

        if ctx.command is None:
            if self.user.id in ctx.message.raw_mentions:
                await self.reply_markov(ctx)
            return

        log.info("user %s used command: %s", message.author, message.content)
        try:
            await self.invoke(ctx)
        except KeyboardInterrupt:
            log.info("User initiated power off, closing")
            await self.close()

    async def reply_markov(self, ctx: context.Context) -> None:
        markov = self.get_command("markov")
        if markov is not None and await markov.can_run(ctx):
            log.info("user %s used markov by mention: %s", ctx.message.author, ctx.message.content)
            await markov(ctx)

    async def on_ready(self) -> None:
        log.info("Bot is now all ready to go")
        self.intorduce()

    async def on_message(self, message: Message) -> None:
        if message.author.bot:
            return
        if isinstance(message.author, User):
            return
        if cast(bool, Config.bot.DEBUG) and not message.author.guild_permissions.administrator:
            return
        await self.process_commands(message)

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        """ reimplement on_error method to print to a log file instead of sys.stderr"""
        log.error(f'Ignoring exception in %s' % (event_method,), exc_info=True)



    def add_cog(self, cog: commands.Cog, *, override: bool = False) -> None:
        log.info("loading cog: %s", cog.qualified_name)
        super().add_cog(cog, override=override)

    def remove_cog(self, name: str) -> None:
        log.info("unloading cog: %s", name)
        super().remove_cog(name)



    def intorduce(self) -> None:
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
        print(f"     [BOT] {bot_name} ready to serve! \n\n\n")
