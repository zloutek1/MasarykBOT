import asyncio
import logging
import traceback
from datetime import datetime, timezone
from collections import Counter

from discord.ext import commands

from bot.constants import Config
from bot.cogs.utils import context

DESCRIPTION = """
$ Hello
"""

log = logging.getLogger(__name__)


class MasarykBOT(commands.Bot):
    def __init__(self, *args, description=DESCRIPTION, **kwargs):
        super().__init__(*args, **kwargs)

        self.spam_control = commands.CooldownMapping.from_cooldown(10, 12.0, commands.BucketType.user)
        self._auto_spam_count = Counter()

        self.db = None
        self.uptime = None

    async def on_ready(self):
        if self.uptime is None:
            self.uptime = datetime.utcnow()

        self.intorduce()

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
        self._auto_spam_count.pop(author_id, None)

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
        super().add_cog(cog)
        log.info("Cog loaded: %s", cog.qualified_name)

    def remove_cog(self, name: str) -> None:
        super().remove_cog(name)
        log.info("Cog unloaded: %s", name)

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
