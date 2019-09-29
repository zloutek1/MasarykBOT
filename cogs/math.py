import discord
from discord.ext import commands

import urllib
import graphviz as gz


class Math(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """---------------------------------------------------------------------------------------------------------------------------"""

    async def get_math_equation(self, equation):
        tex2imgURL = "http://www.sciweavers.org/tex2img.php?eq={}&bc=White&fc=Black&im=png&fs=12&ff=arev&edit=0"

        embed = discord.Embed()
        embed.set_image(url=tex2imgURL.format(urllib.parse.quote(equation)))

        return embed

    @commands.command()
    async def latex(self, ctx, *, equation):
        embed = await self.get_math_equation(equation)
        await ctx.send(embed=embed)

    """---------------------------------------------------------------------------------------------------------------------------"""

    @commands.command(name="digraph", aliases=("graphviz",))
    async def digraph(self, ctx, *, equation):
        src = gz.Source(
            equation,
            format="png")
        src.render('assets/graphviz', view=False)

        await ctx.send(file=discord.File("assets/graphviz.png"))

    def is_graphviz_message(self, body):
        return (body.startswith("```digraph") and
                body.endswith("```") and
                body.count("\n") >= 2)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.is_graphviz_message(message.content):
            return

        if message.author.bot:
            return

        await message.add_reaction("▶")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        message = reaction.message
        if not self.is_graphviz_message(message.content):
            return

        if message.author.bot or user.bot or message.author != user:
            return

        if str(reaction.emoji) != "▶":
            return

        if self.bot.user not in await reaction.users().flatten():
            return

        ctx = commands.Context(prefix=self.bot.command_prefix, guild=message.guild,
                               channel=message.channel, message=message, author=user)
        await self.digraph.callback(self, ctx, equation=message.content.strip("```"))

        await ctx.message.remove_reaction("▶", ctx.author)
        await ctx.message.remove_reaction("▶", self.bot.user)


def setup(bot):
    bot.add_cog(Math(bot))
