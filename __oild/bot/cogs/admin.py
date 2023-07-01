import logging
import os
from datetime import datetime
from typing import NoReturn, Optional

import discord as discord
from discord.ext import commands

from src.bot import Context

log = logging.getLogger(__name__)


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def say(self, ctx: Context, *, content: str) -> None:
        await ctx.send(content)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def purge(self, ctx: Context, limit: int = 0) -> None:
        assert isinstance(ctx.channel, (discord.TextChannel, discord.Thread))
        await ctx.channel.purge(limit=limit + 1)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.is_owner()
    async def shutdown(self, ctx: Context) -> None:
        log.info("Shutting down...")
        await ctx.safe_delete()
        raise KeyboardInterrupt

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.is_owner()
    async def hide(self, ctx: Context) -> None:
        await ctx.safe_delete()
        await self.bot.change_presence(status=discord.Status.invisible)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.is_owner()
    async def show(self, ctx: Context) -> None:
        await ctx.safe_delete()
        await self.bot.change_presence(status=discord.Status.online)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def fail(self, ctx: Context) -> NoReturn:
        raise Exception("failing code for testing purposes")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx: Context) -> None:
        fmt = await ctx.bot.tree.sync()
        await ctx.send(f"synced {len(fmt)} commands")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def logs(self, ctx: Context, filename: Optional[str] = None) -> None:
        await ctx.safe_delete()

        if filename is None:
            await ctx.send("Available log files:\n[-] " + "\n[-] ".join(os.listdir("./logs/")))
            return

        filepath = "./logs/" + os.path.basename(filename)
        if not os.path.exists(filepath):
            await ctx.send("file does not exist")
            return

        filename = os.path.splitext(filename)[0]
        filename += "_" + datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + ".log"
        await ctx.author.send(file=discord.File(filepath, filename))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
