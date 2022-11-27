from typing import Optional

from .utils import Context
from discord.ext import commands


class CogManager(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.last_reloaded: Optional[str] = None

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def load(self, ctx: Context, *, module: str) -> None:
        """Loads a module."""
        await ctx.safe_delete(delay=5.0)
        try:
            await self.bot.load_extension(module)
        except commands.ExtensionError as err:
            await ctx.send_error(f'{err.__class__.__name__}: {err}', delete_after=5.0)
        except ModuleNotFoundError as err:
            await ctx.send_error(f'{err.__class__.__name__}: {err}', delete_after=5.0)
        else:
            await ctx.send_success(f'{module} loaded successfully', delete_after=5.0)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unload(self, ctx: Context, *, module: str) -> None:
        """Unloads a module."""
        await ctx.safe_delete(delay=5.0)
        try:
            await self.bot.unload_extension(module)
        except commands.ExtensionError as err:
            await ctx.send_error(f'{err.__class__.__name__}: {err}', delete_after=5.0)
        except ModuleNotFoundError as err:
            await ctx.send_error(f'{err.__class__.__name__}: {err}', delete_after=5.0)
        else:
            await ctx.send_success(f'{module} unloaded successfully', delete_after=5.0)

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def reload(self, ctx: Context, *, module: Optional[str] = None) -> None:
        """Reloads a module."""

        if module is None:
            if self.last_reloaded is not None:
                await self.reload(ctx, module=self.last_reloaded)
            return

        await ctx.safe_delete(delay=5.0)
        try:
            await self.bot.reload_extension(module)
            self.last_reloaded = module
        except commands.ExtensionError as err:
            await ctx.send_error(f'{err.__class__.__name__}: {err}', delete_after=5.0)
        except ModuleNotFoundError as err:
            await ctx.send_error(f'{err.__class__.__name__}: {err}', delete_after=5.0)
        else:
            await ctx.send_success(f'{module} reloaded successfully', delete_after=5.0)

    @reload.command(name='all', hidden=True)  # type: ignore[arg-type]
    async def reload_all(self, ctx: Context) -> None:
        """Reloads all modules"""
        output = ""

        for module in list(self.bot.extensions.keys()):
            try:
                await self.bot.reload_extension(module)
            except commands.ExtensionError as err:
                output += f'{module} - {err.__class__.__name__}: {err}\n'
            except ModuleNotFoundError as err:
                await ctx.send_error(f'{err.__class__.__name__}: {err}', delete_after=5.0)
            else:
                output += f'{module} - reloaded successfully\n'

        await ctx.safe_delete(delay=5.0)
        await ctx.send_embed(output, delete_after=5.0)

    @commands.command()
    async def cogs(self, ctx: Context) -> None:
        await ctx.send_embed(" **»** " + "\n **»** ".join(self.bot.cogs))

    @commands.command(aliases=["extentions"])
    async def extensions(self, ctx: Context) -> None:
        await ctx.send_embed(" **»** " + "\n **»** ".join(self.bot.extensions))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CogManager(bot))
