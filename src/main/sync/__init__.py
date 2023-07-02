from discord.ext import commands


async def setup(bot: commands.Bot) -> None:
    from sync.cog import Sync

    await bot.add_cog(Sync(bot))
