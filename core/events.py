import discord
from discord import Colour, Embed, Member, Object
from discord.ext import commands
from discord.ext.commands import Bot

import traceback
import datetime

from config import BotConfig
from core.utils.checks import needs_database


class Events(commands.Cog):
    """No commands, just event handlers."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            with open(BotConfig.icon, "rb") as f:
                await self.bot.user.edit(username=BotConfig.name, avatar=f.read())
        except OSError as e:
            print("Failed to set new name and avatar to the bot")
        except discord.errors.HTTPException as e:
            pass

        print("{0.user.name} ready to serve!".format(self.bot))

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("pong!")

    @commands.command()
    async def invite(self, ctx):
        await ctx.send(f"https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=0")

    # https://github.com/python-discord/bot/blob/master/bot/cogs/events.py

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        try:
            await ctx.message.delete()
        except:
            pass

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

        print(message)
        # self.bot.logs['discord'].critical(message)


def setup(bot):
    bot.add_cog(Events(bot))
    print("Cog loaded: Events")
