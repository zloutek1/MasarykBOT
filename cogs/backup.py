import asyncio
import requests

import discord
from discord.ext import commands
from discord import Colour, Embed, Member, Object, File

from datetime import datetime, timedelta

from core.utils.checks import needs_database


class Backup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # check database connection
        if not self.bot.db:
            return

        if (message.author.bot):
            return

        # valid message
        if (message.channel is discord.TextChannel or not message.author or not message.guild or not message.channel.guild):
            return

        for attachment in message.attachments:
            self.bot.db.execute("INSERT INTO backup_attachemnts VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (message.guild.id, str(message.guild), message.channel.id, str(message.channel), message.id, attachment.width, attachment.height, attachment.size, attachment.filename, attachment.url))

        self.bot.db.commit()

    @commands.command()
    @needs_database
    async def backup(self, ctx):
        await ctx.message.delete()

        guild = ctx.guild
        message = ctx.message
        author = message.author
        ch = message.channel

        ctx.db.execute("DELETE FROM backup_attachemnts WHERE guild_id=%s", (guild.id,))
        ctx.db.commit()
        batch = []

        async def get_channel_msg(channel):
            nonlocal batch
            await asyncio.sleep(0)
            with requests.Session() as session:
                async for message in channel.history(limit=1000000):
                    for attachment in message.attachments:
                        batch.append((message.guild.id, str(message.guild), message.channel.id, str(message.channel), message.id, attachment.width, attachment.height, attachment.size, attachment.filename, attachment.url))

                        if len(batch) > 100:
                            self.bot.db.executemany("INSERT INTO backup_attachemnts VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", batch)
                            batch = []

        for channel in guild.channels:
            if not type(channel) is discord.channel.TextChannel:
                continue

            try:
                task = await asyncio.ensure_future(get_channel_msg(channel))
                print("[Backup] -", guild, ": Saved", channel)
            except discord.Forbidden:
                print("[Backup] -", guild, ": Forbidden", channel)

        if len(batch) > 0:
            print(batch)
            ctx.db.executemany("INSERT INTO backup_attachemnts VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", batch)
        ctx.db.commit()

        print("Backup done")


def setup(bot):
    bot.add_cog(Backup(bot))
    print("Cog loaded: Backup")
