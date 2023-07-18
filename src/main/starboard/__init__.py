from discord.ext import commands


async def setup(bot: commands.Bot) -> None:
    from starboard.cog import Starboard

    await bot.add_cog(Starboard(bot))
