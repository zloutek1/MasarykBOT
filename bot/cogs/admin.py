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

    @commands.command()
    @has_permissions(administrator=True)
    async def audit_to_csv(self, ctx, limit: int = None):
        log.info("gettings audit logs for guild %s", ctx.guild)

        counter = 0
        content = "created_at, user, action, target, id, reason\n"
        async for entry in ctx.guild.audit_logs(limit=limit):
            action = str(entry.action).replace("AuditLogAction.", "")
            content += f"{entry.created_at}, {entry.user.name}, {action}, {entry.target}, {entry.id}, {entry.reason}\n"

            if counter % 5_000 == 0:
                log.info("got %s audit logs so far", counter)
            counter += 1

        else:
            log.info("finished with %s audit logs", counter)
            filename = f"audit_logs_{ctx.guild}.csv"
            with open(filename, 'w') as file:
                file.write(content)
            await ctx.send(file=discord.File(filename))


def setup(bot):
    bot.add_cog(Admin(bot))
