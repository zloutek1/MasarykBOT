from discord import Color
from discord.ext import commands


class CogManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def load(self, ctx, *, module):
        """Loads a module."""
        try:
            self.bot.load_extension(module)
        except commands.ExtensionError as e:
            await ctx.send_embed(f'{e.__class__.__name__}: {e}', color=Color.red())
        else:
            await ctx.send_embed(f'{module} loaded successfully', color=Color.green())

    @commands.command(hidden=True)
    async def unload(self, ctx, *, module):
        """Unloads a module."""
        try:
            self.bot.unload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send_embed(f'{e.__class__.__name__}: {e}', color=Color.red())
        else:
            await ctx.send_embed(f'{module} unloaded successfully', color=Color.green())

    @commands.group(name='reload', hidden=True, invoke_without_command=True)
    async def _reload(self, ctx, *, module):
        """Reloads a module."""
        try:
            self.bot.reload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send_embed(f'{e.__class__.__name__}: {e}', color=Color.red())
        else:
            await ctx.send_embed(f'{module} reloaded successfully', color=Color.green())

    @_reload.command(name='all', hidden=True)
    async def _reload_all(self, ctx):
        """Reloads all modules"""
        output = ""

        for module in list(self.bot.extensions.keys()):
            try:
                self.bot.reload_extension(module)
            except commands.ExtensionError as e:
                output += f'{module} - {e.__class__.__name__}: {e}\n'
            else:
                output += f'{module} - reloaded successfully\n'

        await ctx.send_embed(output)

    @commands.command(hidden=True)
    async def cogs(self, ctx):
        await ctx.send_embed(" **»** " + "\n **»** ".join(self.bot.cogs))

    @commands.command(hidden=True, aliases=["extentions"])
    async def extensions(self, ctx):
        await ctx.send_embed(" **»** " + "\n **»** ".join(self.bot.extensions))


def setup(bot):
    bot.add_cog(CogManager(bot))
