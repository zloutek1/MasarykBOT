import logging
from typing import Any, Optional, Union, Type, cast

import discord
from discord import Message, Activity, ActivityType, Interaction, Member
from discord.utils import MISSING
from discord.ext import commands
from discord.ext.commands._types import ContextT

from src.bot import CONFIG
from src.bot import Context

log = logging.getLogger(__name__)


class MasarykBOT(commands.Bot):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.activity = self.activity or Activity(type=ActivityType.listening, name=CONFIG.bot.prefix + "help")

    async def on_ready(self) -> None:
        log.info("Bot is now all ready to go")
        self.introduce()

    async def get_context(self, origin: Union[Message, Interaction], /, *, cls: Type[ContextT] = MISSING) -> Any:
        cls = cast(Type[ContextT], Context) if cls is MISSING else cls
        return await super(MasarykBOT, self).get_context(origin, cls=cls)

    async def process_commands(self, message: Message) -> None:
        def is_admin(user: discord.User | discord.Member) -> bool:
            return isinstance(user, Member) and user.guild_permissions.administrator

        if CONFIG.bot.DEBUG and not is_admin(message.author):
            return

        from __oild.bot.cogs.markov import MarkovCog
        if cog := cast(MarkovCog, self.get_cog("MarkovCog")):
            if await cog.markov_from_message(message):
                return

        await super(MasarykBOT, self).process_commands(message)

    @staticmethod
    async def on_command(ctx: Context) -> None:
        if ctx.message.content:
            command = ctx.message.content
            log.info(f'in #{ctx.channel} @{ctx.author} used command: {command}')
        else:
            params = ' '.join(map(str, ctx.kwargs.values()))
            command = f"{ctx.prefix}{ctx.command} {params}"
            log.info(f'in #{ctx.channel} @{ctx.author} used slash command: {command}')

    async def add_cog(self, cog: commands.Cog, *args: Any, **kwargs: Any) -> None:
        log.info("loading cog: %s", cog.qualified_name)
        return await super().add_cog(cog, *args, **kwargs)

    async def remove_cog(self, name: str, *args: Any, **kwargs: Any) -> Optional[commands.Cog]:
        log.info("unloading cog: %s", name)
        return await super().remove_cog(name, *args, **kwargs)

    def introduce(self) -> None:
        assert self.user, "no user"
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
