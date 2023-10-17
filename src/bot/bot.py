import logging
from typing import Any

import discord
from discord.ext import commands


__all__ = ['MasarykBOT']


log = logging.getLogger(__name__)


class MasarykBOT(commands.Bot):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.activity = self.activity or discord.Activity(type=discord.ActivityType.listening, name="!help")

    async def on_ready(self) -> None:
        log.info("Bot is now all ready to go")
        print("Hello there, I am ready")

