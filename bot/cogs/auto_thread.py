from urllib.request import urlopen
from lxml.html import parse


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

        title = message.content.split("\n")[0]
        if "http://" in title or "https://" in title:
            url = title
            page = urlopen(url)
            p = parse(page)
            title = p.find(".//title").text

        title = title[:50] + "..." if len(title) > 50 else title
        await message.create_thread(name=title)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(AutoThread(bot))
