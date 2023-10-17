from discord.ext import commands

from .echo_service import EchoService


class EchoCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.service = EchoService(bot)

    @commands.command()
    async def echo(self, ctx, message: str):
        await self.service.echo(ctx, message)


async def setup(bot):
    await bot.add_cog(EchoCog(bot))