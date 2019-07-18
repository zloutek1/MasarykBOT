from discord import Colour, Embed, Member, Object
from discord.ext import commands
from discord.ext.commands import Bot

from config import BotConfig


class Events(commands.Cog):
    """No commands, just event handlers."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("{0.user.name} ready to serve!".format(self.bot))

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("pong!")

    # https://github.com/python-discord/bot/blob/master/bot/cogs/events.py


def setup(bot):
    bot.add_cog(Events(bot))
    print("Cog loaded: Events")
