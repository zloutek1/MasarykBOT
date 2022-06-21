from disnake import (Message)
from disnake.utils import get
from disnake.ext import commands

from bot.constants import Config

class AutoThread(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        guild_config = get(Config.guilds, id = message.guild.id)
        if guild_config is None:
            return

        threaded_channels = guild_config.channels.threaded
        if message.channel.id not in threaded_channels:
            return

        await message.create_thread(name=message.content[:50])


def setup(bot: commands.Bot) -> None:
    bot.add_cog(AutoThread(bot))
