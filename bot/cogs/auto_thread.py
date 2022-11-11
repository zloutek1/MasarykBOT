from typing import cast
from urllib.request import urlopen
from lxml.html import parse

from discord import Message
from discord.abc import Messageable, GuildChannel
from discord.utils import get
from discord.ext import commands

from bot.constants import CONFIG


class AutoThreadService:
    @staticmethod
    def is_threaded_channel(channel: Messageable) -> bool:
        if not isinstance(channel, GuildChannel):
            return False

        if not (guild := channel.guild):
            return False

        if not (guild_config := get(CONFIG.guilds, id = guild.id)):
            return False

        threaded_channels = guild_config.channels.threaded
        return channel.id in threaded_channels


    @staticmethod
    def extract_thread_title(message: Message) -> str:
        title = message.content.split("\n")[0]
        if "http://" in title or "https://" in title:
            url = title
            page = urlopen(url)
            p = parse(page)
            title = cast(str, p.find(".//title").text)

        return title[:50] + "..." if len(title) > 50 else title



class AutoThread(commands.Cog):
    service = AutoThreadService()

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        assert message.guild, "can only be used in guilds"

        if not self.service.is_threaded_channel(message.channel):
            return
        
        title = self.service.extract_thread_title(message)
        await message.create_thread(name=title)



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AutoThread(bot))
