import discord
from discord.ext import commands

import urllib


class Math(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_math_equasion(self, equasion):
        tex2imgURL = "http://www.sciweavers.org/tex2img.php?eq={}&bc=White&fc=Black&im=png&fs=12&ff=arev&edit=0"

        embed = discord.Embed()
        embed.set_image(url=tex2imgURL.format(urllib.parse.quote(equasion)))

        return embed

    @commands.command()
    async def latex(self, ctx, *equasion):
        embed = await self.get_math_equasion(equasion)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Math(bot))
