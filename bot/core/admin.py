import discord
from discord import Colour, Embed, Member, Object
from discord.ext import commands
from discord.ext.commands import Bot, has_permissions

import os
import json

from config import BotConfig


class Admin(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    @has_permissions(administrator=True)
    async def purge(self, ctx, limit: int = 0):
        await ctx.channel.purge(limit=limit + 1)

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

        del_cat = True
        for channel in category.channels:
            if not channel.last_message_id:
                await channel.delete()
            else:
                del_cat = False
        if del_cat:
            await category.delete()

    @commands.group(name="log_channel")
    @has_permissions(manage_channels=True)
    async def log_channel(self, ctx):
        pass

    @log_channel.command(name="set")
    async def log_channel_set(self, ctx):
        with open("assets/local_db.json", "r", encoding="utf-8") as file:
            local_db = json.load(file)
            local_db.setdefault("log_channels", [])
            if ctx.channel.id not in local_db["log_channels"]:
                local_db["log_channels"].append(ctx.channel.id)

        with open("assets/local_db.json", "w", encoding="utf-8") as file:
            json.dump(local_db, file)

        await ctx.delete()
        await ctx.send("Log Channel set successfully", delete_after=5)

    @commands.group(name="error_channel")
    @has_permissions(manage_channels=True)
    async def error_channel(self, ctx):
        pass

    @error_channel.command(name="set")
    async def error_channel_set(self, ctx):
        with open("assets/local_db.json", "r", encoding="utf-8") as file:
            local_db = json.load(file)
            local_db.setdefault("error_channels", [])
            if ctx.channel.id not in local_db["error_channels"]:
                local_db["error_channels"].append(ctx.channel.id)

        with open("assets/local_db.json", "w", encoding="utf-8") as file:
            json.dump(local_db, file)

        await ctx.delete()
        await ctx.send("Log Channel set successfully", delete_after=5)


def setup(bot):
    bot.add_cog(Admin(bot))
