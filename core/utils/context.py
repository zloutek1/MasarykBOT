from discord.ext import commands
import asyncio
import discord

import core.utils.get
from core.utils import db
from core.utils.db import Database

from config import BotConfig


class Context(commands.Context):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_channel(self, name):
        return core.utils.get(self.guild.channels, name=name)

    def get_role(self, name):
        return core.utils.get(self.guild.roles, name=name)

    def get_emoji(self, name):
        return core.utils.get(self.bot.emojis, name=name)
