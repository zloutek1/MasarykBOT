from discord.ext import commands


class Admin(commands.Cog):
    """Admin-only commands that make the bot dynamic."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def load(self, ctx, *, module):
        """Loads a module."""
        try:
            self.bot.load_extension(module)
        except commands.ExtensionError as e:
            await ctx.send_embed(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.send_embed(f'{module} loaded successfully')

    @commands.command(hidden=True)
    async def unload(self, ctx, *, module):
        """Unloads a module."""
        try:
            self.bot.unload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send_embed(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.send_embed(f'{module} unloaded successfully')

    @commands.group(name='reload', hidden=True, invoke_without_command=True)
    async def _reload(self, ctx, *, module):
        """Reloads a module."""
        try:
            self.bot.reload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send_embed(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.send_embed(f'{module} reloaded successfully')

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


def setup(bot):
    bot.add_cog(Admin(bot))
