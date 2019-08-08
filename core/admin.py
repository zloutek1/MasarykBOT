import discord
from discord import Colour, Embed, Member, Object
from discord.ext import commands
from discord.ext.commands import Bot, has_permissions

import os

from config import BotConfig


class Admin(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    @has_permissions(administrator=True)
    async def purge(self, ctx, limit: int):
        await ctx.channel.purge(limit=100)

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command(aliases=['clearconsole', 'cc', 'clear'])
    @has_permissions(administrator=True)
    async def cleartrace(self, ctx):
        """Clear the console."""
        if os.name == 'nt':
            os.system('cls')
        else:
            try:
                os.system('clear')
            except Exception:
                for _ in range(100):
                    print()

        self.bot.intorduce()
        await ctx.send('Console cleared successfully.', delete_after=5)

        await ctx.message.delete()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    @has_permissions(administrator=True)
    async def purge_category(self, ctx, category_id: int):
        await ctx.message.delete()

        category = ctx.guild.get_channel(category_id)
        if not isinstance(category, discord.channel.CategoryChannel):
            await ctx.send("channel is not a category", delete_after=5)

        for channel in category.channels:
            await channel.delete()
        await category.delete()


def setup(bot):
    bot.add_cog(Admin(bot))
    print("Cog loaded: Admin")
