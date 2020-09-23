from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role("Admin")
    async def say(self, ctx, *, content: str):
        await ctx.send(content)


def setup(bot):
    bot.add_cog(Admin(bot))
