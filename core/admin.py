from discord import Colour, Embed, Member, Object
from discord.ext import commands
from discord.ext.commands import Bot, has_permissions

import os

from config import BotConfig


class Admin(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    @has_permissions(administrator=True)
    async def purge(self, ctx, limit: int):
        await ctx.channel.purge(limit=100)

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

        message = 'Logged in as %s.' % self.bot.user
        try:
            print(message)
        except Exception as e:  # some bot usernames with special chars fail on shitty platforms
            print(message.encode(errors='replace').decode())
        await ctx.send('Console cleared successfully.', delete_after=5)

        await ctx.message.delete()


def setup(bot):
    bot.add_cog(Admin(bot))
    print("Cog loaded: Admin")
