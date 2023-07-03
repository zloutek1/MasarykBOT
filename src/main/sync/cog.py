from dependency_injector.wiring import Provide
from discord.ext import commands

from core.context.__init__ import Context
from core.inject import Inject


class Sync(commands.Cog):
    sync_guilds = Provide[Inject.config.bot.cogs.sync.guilds]
    syncers = Provide[Inject.syncer.all]

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        print(self.syncers)

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx: Context) -> None:
        guilds = [self.bot.get_guild(guild_id) for guild_id in self.sync_guilds]

        for syncer in self.syncers:
            for guild in guilds:
                await syncer.sync(guild, ctx)
