import io
import logging
import os
from contextlib import suppress
from datetime import datetime
from typing import NoReturn, Optional

import disnake as discord
from disnake.errors import NotFound
from disnake.ext import commands
from disnake.ext.commands import has_permissions

from .utils.context import Context

log = logging.getLogger(__name__)

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    @has_permissions(administrator=True)
    async def say(self, ctx: Context, *, content: str) -> None:
        await ctx.send(content)

    @commands.command()
    @has_permissions(administrator=True)
    async def purge(self, ctx: Context, limit: int = 0) -> None:
        assert isinstance(ctx.channel, (discord.TextChannel, discord.Thread))
        await ctx.channel.purge(limit=limit + 1)

    @commands.command()
    @has_permissions(administrator=True)
    @commands.is_owner()
    async def shutdown(self, ctx: Context) -> None:
        log.info("Shutting down...")
        with suppress(NotFound):
            await ctx.message.delete()
        raise KeyboardInterrupt

    @commands.command()
    @has_permissions(administrator=True)
    @commands.is_owner()
    async def hide(self, ctx: Context) -> None:
        await self.bot.change_presence(status=discord.Status.invisible)
        await ctx.safe_delete()

    @commands.command()
    @has_permissions(administrator=True)
    @commands.is_owner()
    async def show(self, ctx: Context) -> None:
        await self.bot.change_presence(status=discord.Status.online)
        await ctx.safe_delete()

    @commands.command()
    @has_permissions(administrator=True)
    async def audit_to_csv(self, ctx: Context, limit: int = 100) -> None:
        assert ctx.guild

        log.info("gettings audit logs for guild %s", ctx.guild)

        counter = 0
        content = "created_at, user, action, target, id, reason\n"
        async for entry in ctx.guild.audit_logs(limit=limit):
            action = str(entry.action).replace("AuditLogAction.", "")
            content += ", ".join(map(str, [
                entry.created_at,
                entry.user and entry.user.name,
                action,
                entry.target,
                entry.id,
                entry.reason
            ])) + "\n"

            if counter % 5_000 == 0:
                log.info("got %s audit logs so far", counter)
            counter += 1

        else:
            log.info("finished with %s audit logs", counter)
            filename = f"audit_logs_{ctx.guild}.csv"
            with open(filename, 'w') as file:
                file.write(content)
            await ctx.send(file=discord.File(filename))

    @commands.command()
    @has_permissions(administrator=True)
    async def fail(self, ctx: Context) -> NoReturn:
        raise Exception("failing code for testing purposes")

    @commands.command()
    @has_permissions(administrator=True)
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


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Admin(bot))
