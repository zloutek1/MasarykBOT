import discord
from discord.ext import commands
from discord import Colour, Embed, Member, Object, File


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def emoji_list(self, ctx):
        await ctx.message.delete()

        emojis = sorted(ctx.guild.emojis, key=lambda emoji: emoji.name)
        for i in range(0, len(emojis), 10):
            await ctx.send(" ".join(list(map(str, emojis[i:i + 10]))))


def setup(bot):
    bot.add_cog(Fun(bot))
    print("Cog loaded: Fun")
