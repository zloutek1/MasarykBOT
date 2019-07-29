import discord
from discord.ext import commands
from discord import Colour, Embed, Member, Object, File


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def verify(self, ctx):
        print(ctx.author.name)


def setup(bot):
    bot.add_cog(Verification(bot))
    print("Cog loaded: Verification")
