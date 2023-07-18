import discord
from discord.ext import commands

from core.context import Context
from starboard.service import StarableChannel, StarboardService


class Starboard(commands.Cog):
    def __init__(self, bot: commands.Bot, service: StarboardService = None) -> None:
        self.bot = bot
        self.service = service if service else StarboardService(bot)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        await self.service.reaction_added(payload)

    @commands.hybrid_group()
    async def starboard(self, ctx: Context):
        pass

    @starboard.command()
    async def create(self, ctx: Context, *, name: str = "starboard"):
        await ctx.defer()

        message = await self.service.create(ctx, name)
        await ctx.send(message)

    @starboard.command()
    async def redirect(
            self,
            ctx: Context,
            starboard_channel: discord.TextChannel,
            targets: commands.Greedy[StarableChannel | discord.Member]
    ):
        await ctx.defer()

        message = await self.service.redirect(ctx, targets, starboard_channel)
        await ctx.send(message)
