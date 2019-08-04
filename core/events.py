import discord
from discord import Colour, Embed, Member, Object
from discord.ext import commands
from discord.ext.commands import Bot

from config import BotConfig
from core.utils.checks import needs_database


class Events(commands.Cog):
    """No commands, just event handlers."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("{0.user.name} ready to serve!".format(self.bot))

        try:
            with open(BotConfig.icon, "rb") as f:
                await self.bot.user.edit(username=BotConfig.name, avatar=f.read())
        except OSError as e:
            print("Failed to set new name and avatar to the bot")
        except discord.errors.HTTPException as e:
            pass

        # check database connection
        if not self.bot.db:
            return

        self.bot.db.executemany("INSERT IGNORE INTO guilds (id, name) VALUES (%s, %s)", [(guild.id, guild.name) for guild in self.bot.guilds])

        self.bot.db.executemany("INSERT IGNORE INTO channels (guild_id, id, name) VALUES (%s, %s, %s)", [(guild.id, channel.id, channel.name) for guild in self.bot.guilds for channel in guild.channels if isinstance(channel, discord.channel.TextChannel)])

        self.bot.db.executemany("INSERT IGNORE INTO members (id, name, nickname) VALUES (%s, %s, %s)", [(member.id, member.name, member.nick) for guild in self.bot.guilds for member in guild.members])
        self.bot.db.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # check database connection
        if not self.bot.db:
            return

        self.bot.db.execute("INSERT IGNORE INTO members (id, name, nickname) VALUES (%s, %s, %s)", (member.id, member.name, member.nick))
        self.bot.db.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # check database connection
        if not self.bot.db:
            return

        self.bot.db.execute("INSERT IGNORE INTO members (id, name, nickname) VALUES (%s, %s, %s)", (member.id, member.name, member.nick))
        self.bot.db.commit()

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # check database connection
        if not self.bot.db:
            return

        if before.nick != after.nick:
            self.bot.db.execute("INSERT IGNORE INTO members (id, name, nickname) VALUES (%s, %s, %s)", (member.id, member.name, member.nick))
            self.bot.db.commit()

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("pong!")

    # https://github.com/python-discord/bot/blob/master/bot/cogs/events.py

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await ctx.message.delete()

        ignored = (
            commands.NoPrivateMessage, commands.DisabledCommand, commands.CheckFailure,
            commands.CommandNotFound, commands.UserInputError, discord.HTTPException
        )
        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        if ctx.message.server:
            fmt = 'Channel: {0} (ID: {0.id})\nGuild: {1} (ID: {1.id})'
        else:
            fmt = 'Channel: {0} (ID: {0.id})'

        exc = traceback.format_exception(type(error), error, error.__traceback__, chain=False)
        description = '```py\n%s\n```' % ''.join(exc)
        time = datetime.datetime.utcnow()

        name = ctx.command.qualified_name
        author = '{0} (ID: {0.id})'.format(ctx.message.author)
        location = fmt.format(ctx.message.channel, ctx.message.server)

        message = '{0} at {1}: Called by: {2} in {3}. More info: {4}'.format(name, time, author, location, description)

        # self.bot.logs['discord'].critical(message)


def setup(bot):
    bot.add_cog(Events(bot))
    print("Cog loaded: Events")
