from dependency_injector.wiring import Provide
from discord.ext import commands

from core.context import Context
from core.inject import Inject


class Sync(commands.Cog):
    sync_guilds = Provide[Inject.config.bot.cogs.sync.guilds]

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command()
    async def sync(self, ctx: Context) -> None:
        await ctx.send("hello")
