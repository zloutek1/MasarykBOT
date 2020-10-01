import logging

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions

log = logging.getLogger(__name__)

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role("Admin")
    async def say(self, ctx, *, content: str):
        await ctx.send(content)

    @commands.command()
    @has_permissions(administrator=True)
    async def purge(self, ctx, limit: int = 0):
        await ctx.channel.purge(limit=limit + 1)

    @commands.command()
    @has_permissions(administrator=True)
    @commands.is_owner()
    async def shutdown(self, ctx):
        log.info("Shutting down...")
        await ctx.message.delete()
        raise KeyboardInterrupt

    @commands.command()
    @has_permissions(administrator=True)
    @commands.is_owner()
    async def hide(self, ctx):
        await self.bot.change_presence(status=discord.Status.invisible)
        await ctx.safe_delete()

    @commands.command()
    @has_permissions(administrator=True)
    @commands.is_owner()
    async def show(self, ctx):
        await self.bot.change_presence(status=discord.Status.online)
        await ctx.safe_delete()

def setup(bot):
    bot.add_cog(Admin(bot))
