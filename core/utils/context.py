from discord.ext import commands

import core.utils.get
import re


class Context(commands.Context):
    """
    custom Context object passed in every ctx variable
    in your commands. provides some useful getter shortcuts
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_category(self, name=None, **kwargs):
        kwargs.update({"name": name}) if name is not None else None
        return core.utils.get(self.guild.categories, **kwargs)

    def get_channel(self, name=None, **kwargs):
        kwargs.update({"name": name}) if name is not None else None
        return core.utils.get(self.guild.channels, **kwargs)

    def get_role(self, name=None, **kwargs):
        kwargs.update({"name": name}) if name is not None else None
        return core.utils.get(self.guild.roles, **kwargs)

    def get_emoji(self, name=None, **kwargs):
        kwargs.update({"name": name}) if name is not None else None
        return core.utils.get(self.bot.emojis, **kwargs)

    def get_user(self, name=None, **kwargs):
        kwargs.update({"name": name}) if name is not None else None
        return core.utils.get(self.guild.members, **kwargs)

    def channel_name(self, text):
        return re.sub("[^a-zA-Z0-9\-]", "", "-".join(text.lower().split()))
