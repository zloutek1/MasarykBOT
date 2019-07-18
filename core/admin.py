from discord import Colour, Embed, Member, Object
from discord.ext import commands
from discord.ext.commands import Bot, has_permissions

from config import BotConfig


class Admin(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    @has_permissions(administrator=True)
    async def purge(self, ctx, limit: int):
        await ctx.channel.purge(limit=100)


def setup(bot):
    bot.add_cog(Admin(bot))
    print("Cog loaded: Admin")
