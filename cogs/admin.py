import discord
from discord import Embed, TextChannel, VoiceChannel, CategoryChannel
from discord.ext import commands
from discord.ext.commands import Bot, has_permissions

import os
import json
import logging
import asyncio

from core.utils.checks import safe


class Admin(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.log = logging.getLogger(__name__)

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
        """
        delete a category with all channels withing the category
        and the category with id of category_id as well
        """
        await ctx.message.delete()

        category = ctx.guild.get_channel(category_id)
        if not isinstance(category, discord.channel.CategoryChannel):
            await ctx.send("channel is not a category", delete_after=5)

        del_cat = True
        for channel in category.channels:
            if isinstance(channel, TextChannel) and not channel.last_message_id:
                await channel.delete()
            elif isinstance(channel, VoiceChannel):
                await channel.delete()
            else:
                del_cat = False
        if del_cat:
            await category.delete()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.group(name="getlogs", aliases=("logs", "getlog"))
    @has_permissions(administrator=True)
    async def getlogs(self, ctx):
        """
        read the file masaryk.log and send
        the last 10 lines to the channel
        """
        with open("assets/masaryk.log", "r") as file:
            lines = file.read().splitlines()
            self.last_log_lines = lines[-10:]
            embed = Embed(title="Log", description="\n".join(
                self.last_log_lines))
            self.logmsg = await ctx.send(embed=embed)

    @getlogs.command(name="-f", aliases=("--follow",))
    async def follow(self, ctx):
        """
        read the file masaryk.log and send
        the last 10 lines to the channel
        update the message every 2 seconds unless
        a change does not happen for 200 seconds
        """
        attempts = 0
        while True:
            with open("assets/masaryk.log", "r") as file:
                lines = file.read().splitlines()
                new_last_lines = lines[-10:]
                if new_last_lines != self.last_log_lines:
                    embed = Embed(
                        title="Log", description="\n".join(new_last_lines))
                    await self.logmsg.edit(embed=embed)
                await asyncio.sleep(2)
            attempts += 1

            if attempts > 100:
                break

    @getlogs.command(name="ready")
    async def ready(self, ctx):
        await ctx.send("```" + str(self.bot.readyCogs) + "```")

    """--------------------------------------------------------------------------------------------------------------------------"""

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

        await ctx.message.delete()
        await ctx.send("Log Channel set successfully", delete_after=5)

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    @has_permissions(manage_channels=True)
    async def sync_category(self, ctx, category: CategoryChannel):
        for channel in category.channels:
            await channel.edit(sync_permissions=True)
        await safe(ctx.message.delete)()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    @has_permissions(administrator=True)
    async def load(self, ctx, extension):
        """
        load the extension to the bot
        save it into the loaded_cogs.json file
        """
        self.bot.load_extension(extension)

        with open("assets/loaded_cogs.json", "r") as fileR:
            with open("assets/loaded_cogs.json", "w") as fileW:
                cogs = json.load(fileR)
                cogs = list(set(cogs) | {extension})  # union
                fileW.write(json.dumps(cogs))

        self.log.info(f"Loaded {extension} successfully")
        await ctx.send(f"Loaded {extension} successfully", delete_after=5)

    @commands.command()
    @has_permissions(administrator=True)
    async def unload(self, ctx, extension):
        """
        unload the extension to the bot
        remove it from the loaded_cogs.json file
        """
        self.bot.unload_extension(extension)

        with open("assets/loaded_cogs.json", "r") as fileR:
            with open("assets/loaded_cogs.json", "w") as fileW:
                cogs = json.load(fileR)
                cogs = list(set(cogs) ^ {extension})  # difference
                fileW.write(json.dumps(cogs))

        self.log.info(f"Unloaded {extension} successfully")
        await ctx.send(f"Unloaded {extension} successfully", delete_after=5)

    @commands.command()
    @has_permissions(administrator=True)
    async def reload(self, ctx, extension=None):
        """
        reload single extension if provided
        otherwise reload all extensions
        """
        if extension is not None:
            self.bot.unload_extension(extension)
            self.bot.load_extension(extension)

            self.log.info(f"Reloaded {extension} successfully")
            await ctx.send(f"Reloaded {extension} successfully", delete_after=5)

        else:
            for extension in self.bot.extensions:
                self.bot.unload_extension(extension)
                self.bot.load_extension(extension)

            self.log.info(f"All extensions successfully")
            await ctx.send(f"All extensions successfully", delete_after=5)

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    @has_permissions(administrator=True)
    async def shutdown(self, ctx):
        self.log.info("Shutting down...")
        await ctx.message.delete()
        raise KeyboardInterrupt


def setup(bot):
    bot.add_cog(Admin(bot))
