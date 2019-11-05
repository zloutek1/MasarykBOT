import os
import discord
from discord.ext import commands

import urllib
import graphviz as gz

from typing import Optional
from sympy import symbols, simplify
from sympy.plotting import plot


class Math(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """---------------------------------------------------------------------------------------------------------------------------"""

    async def get_math_equation(self, equation):
        """
        send the text equasion to the API
        send the result image to channel
        """
        tex2imgURL = "http://www.sciweavers.org/tex2img.php?eq={}&bc=Black&fc=White&im=png&fs=18&ff=arev&edit=0"
        urllib.request.urlretrieve(tex2imgURL.format(urllib.parse.quote(equation)),
                                   "assets/latex.png")

        return discord.File("assets/latex.png")

    @commands.command()
    async def latex(self, ctx, *, equation):
        embed = await self.get_math_equation(equation)
        await ctx.send(file=embed)
        os.remove("assets/latex.png")

    """---------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    async def plot(self, ctx, from_: Optional[float]=-10, to_: Optional[float]=10, *, inp: str):
        """
            !plot from_range to_range equation1; equation2; equation3; ...

            example:
                !plot -10 10 x^2; x^3; x^4
        """
        try:
            x, y = symbols('x y')
            equations = inp.split(";")
            fx = plot(*[simplify(eq)
                        for eq in equations], (x, from_, to_), show=False)

            fx.save("assets/plot.png")
            await ctx.send(file=discord.File("assets/plot.png"))
            os.remove("assets/plot.png")

        except Exception as e:
            await ctx.send(f"{e}")

    """---------------------------------------------------------------------------------------------------------------------------"""

    @commands.command(name="digraph", aliases=("graphviz",))
    async def digraph(self, ctx, *, equasion):
        """
        input equasion in dishraph format into graphviz
        save the file into assets/graphviz.png
        send the file to channel
        """
        src = gz.Source(
            equasion,
            format="png")
        src.render('assets/graphviz', view=False)

        await ctx.send(file=discord.File("assets/graphviz.png"))

    def is_graphviz_message(self, body):
        return (body.startswith("```digraph") and
                body.endswith("```") and
                body.count("\n") >= 2)

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        if message is disgraph compatible
        add the execution (play) button
        """
        if not self.is_graphviz_message(message.content):
            return

        if message.author.bot:
            return

        await message.add_reaction("▶")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """
        check if users clicked the play button on executable code
        the bot has to be a reactor on the executable message
        """

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
