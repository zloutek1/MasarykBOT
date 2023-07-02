from discord.ext import commands


async def setup(bot: commands.Bot) -> None:
    from .cog import ErrorReporter

    await bot.add_cog(ErrorReporter(bot))
