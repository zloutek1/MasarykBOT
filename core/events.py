import discord
from discord import Colour, Embed, Member, Object
from discord.ext import commands
from discord.ext.commands import Bot

from config import BotConfig


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

        self.bot.db.executemany("INSERT IGNORE INTO guilds (guild_id, guild) VALUES (%s, %s)", [(guild.id, guild.name) for guild in self.bot.guilds])

        self.bot.db.executemany("INSERT IGNORE INTO channels (guild_id, channel_id, channel) VALUES (%s, %s, %s)", [(guild.id, channel.id, channel.name) for guild in self.bot.guilds for channel in guild.channels])
        self.bot.db.commit()

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("pong!")

    # https://github.com/python-discord/bot/blob/master/bot/cogs/events.py


def setup(bot):
    bot.add_cog(Events(bot))
    print("Cog loaded: Events")
