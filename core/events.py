import discord
from discord import Color, Embed, Member, Object
from discord.ext import commands
from discord.ext.commands import Bot

import traceback
import datetime
import json

from config import BotConfig
from core.utils import db


class Events(commands.Cog):
    """No commands, just event handlers."""

    def __init__(self, bot: Bot):
        self.bot = bot

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.readyCogs[self.__class__.__name__] = False

        """
        try:
            with open(BotConfig.icon, "rb") as f:
                await self.bot.user.edit(username=BotConfig.name, avatar=f.read())
            print("\n    [Events] username and avatar changed successfully\n")

        except OSError as e:
            print("\nERR [Events] Failed to set new name and avatar to the botn")

        except discord.errors.HTTPException as e:
            pass
        """

        self.bot.readyCogs[self.__class__.__name__] = True

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("pong!")

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    async def invite(self, ctx):
        await ctx.send(f"https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=0")

    # https://github.com/python-discord/bot/blob/master/bot/cogs/events.py

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        ignored = (
            commands.NoPrivateMessage, commands.DisabledCommand, commands.CheckFailure,
            commands.CommandNotFound, commands.UserInputError
        )
        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        if ctx.message.guild:
            fmt = 'Channel: {0} (ID: {0.id})\nGuild: {1} (ID: {1.id})'
        else:
            fmt = 'Channel: {0} (ID: {0.id})'

        exc = traceback.format_exception(type(error), error, error.__traceback__, chain=False)
        description = '```py\n%s\n```' % ''.join(exc)
        time = datetime.datetime.utcnow()

        name = ctx.command.qualified_name
        author = '{0} (ID: {0.id})'.format(ctx.message.author)
        location = fmt.format(ctx.message.channel, ctx.message.guild)

        message = '{0} at {1}: Called by: {2} in {3}. More info: {4}'.format(name, time, author, location, description)
        embed = Embed(
            title='{0} at {1}: Called by: {2} in {3}. More info:'.format(name, time, author, location),
            description=description,
            color=Color.red()
        )

        with open("assets/local_db.json", "r", encoding="utf-8") as file:
            local_db = json.load(file)
            for channel_id in local_db["log_channels"]:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)

        print(message)


def setup(bot):
    bot.add_cog(Events(bot))
