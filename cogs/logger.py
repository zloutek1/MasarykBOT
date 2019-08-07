import asyncio
import requests

import discord
from discord.ext import commands
from discord import Colour, Embed, Member, Object, File
from discord.ext.commands import has_permissions

from datetime import datetime, timedelta

import core.utils.get
from core.utils.checks import needs_database


class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_messages(self, channel, since, message_data, attachment_data, messages_insert, attachment_insert):
        until = datetime.now()

        try:
            async for message in channel.history(limit=10000, after=since, before=until, oldest_first=True):

                # -- Message --
                message_data += [(message.channel.id, message.author.id, message.id, message.content, message.created_at)]

                # insert into SQL
                if len(message_data) > 100:
                    messages_insert(message_data)
                    message_data.clear()

                # -- Attachment --
                for attachment in message.attachments:
                    attachment_data += [(message.id, attachment.id, attachment.filename, attachment.url)]

                    # insert into SQL
                    if len(attachment_data) > 100:
                        attachment_insert(attachment_data)
                        attachment_data.clear()

        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.db.connect():
            return

        print("[Logger] Starting to get up to date with the guilds")

        # get discord objects
        guilds = self.bot.guilds
        categories = [category for guild in guilds for category in guild.categories]
        channels = [channel for guild in guilds for channel in guild.text_channels]
        members = [member for guild in guilds for member in guild.members]
        webhooks = [webhook for guild in guilds for webhook in await guild.webhooks()]

        # get SQL data
        guild_data = [(guild.id, guild.name, str(guild.icon_url))
                      for guild in guilds]
        category_data = [(category.guild.id, category.id, category.name, category.position)
                         for category in categories]
        channel_data = [(channel.guild.id, channel.category_id, channel.id, channel.name, channel.position)
                        for channel in channels]
        member_data = ([(member.id, member.name, str(member.avatar_url))
                        for member in members] +
                       [(webhook.id, webhook.name, str(webhook.avatar_url))
                        for webhook in webhooks])

        # insert into SQL
        self.bot.db.executemany("INSERT INTO guild (id, name, icon_url) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE id=id", guild_data)
        self.bot.db.executemany("INSERT INTO category (guild_id, id, name, position) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE id=id", category_data)
        self.bot.db.executemany("INSERT INTO channel (guild_id, category_id, id, name, position) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE id=id", channel_data)
        self.bot.db.executemany("INSERT INTO `member` (id, name, avatar_url) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE id=id", member_data)
        self.bot.db.commit()

        # console print
        print("[Logger] Updated database values for:")
        print(" - guilds")
        print(" - categories")
        print(" - channels")
        print(" - members")
        print()

        # get SQL data
        message_data = []
        attachment_data = []

        # get last send message time in each channel
        self.bot.db.execute("SELECT channel_id, MAX(created_at) AS created_at FROM (SELECT * FROM `message` WHERE 1) AS res1 GROUP BY channel_id")
        rows = self.bot.db.fetchall()

        def messages_insert(message_data):
            self.bot.db.executemany("INSERT INTO message (channel_id, author_id, id, content, created_at) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE id=id", message_data)
            self.bot.db.commit()

        def attachment_insert(attachment_data):
            self.bot.db.executemany("INSERT INTO attachment (message_id, id, filename, url) VALUES (%s, %s, %s, %s)", attachment_data)
            self.bot.db.commit()

        # insert messages into database
        for channel in channels:
            row = core.utils.get(rows, channel_id=channel.id)
            since = row["created_at"] if row is not None else None

            await self.log_messages(channel, since, message_data, attachment_data, messages_insert, attachment_insert)

        # insert leftovers
        if len(message_data) > 0:
            messages_insert(message_data)
        if len(attachment_data) > 0:
            attachment_insert(attachment_data)

        # console print
        print("[Logger] Updated database values for:")
        print(" - messages")
        print(" - attachemnts")
        print()

        print("[Logger] Bot caught up and is up to date")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.bot.db.connect():
            return

        self.bot.db.execute("INSERT INTO message (channel_id, author_id, id, content, created_at) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE id=id", (message.channel.id, message.author.id, message.id, message.content, message.created_at))

        for attachment in message.attachments:
            self.bot.db.execute("INSERT INTO attachment (message_id, id, filename, url) VALUES (%s, %s, %s, %s)", (message.id, attachment.id, attachment.filename, attachment.url))

        self.bot.db.commit()

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not self.bot.db.connect():
            return

        self.bot.db.execute("UPDATE message SET deleted = true WHERE id = %s", (message.id,))
        self.bot.db.commit()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if not self.bot.db.connect():
            return

        self.bot.db.execute("INSERT INTO guild (id, name, icon_url) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE id=id", (guild.id, guild.name, str(guild.icon_url)))
        self.bot.db.commit()

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        if not self.bot.db.connect():
            return

        self.bot.db.execute("UPDATE guild SET name = %s, icon_url = %s WHERE id = %s", (after.name, str(after.icon_url), after.id))
        self.bot.db.commit()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if not self.bot.db.connect():
            return

        self.bot.db.execute("UPDATE guild SET deleted = true WHERE id = %s", (guild.id,))
        self.bot.db.commit()

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if not self.bot.db.connect():
            return

        if isinstance(channel, discord.channel.TextChannel):
            self.bot.db.execute("INSERT INTO channel (guild_id, category_id, id, name, position) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE id=id", (channel.guild.id, channel.category_id, channel.id, channel.name, channel.position))

        elif isinstance(channel, discord.channel.CategoryChannel):
            self.bot.db.execute("INSERT INTO category (guild_id, id, name, position) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE id=id", (channel.guild.id, channel.id, channel.name, channel.position))

        self.bot.db.commit()

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if not self.bot.db.connect():
            return

        if isinstance(after, discord.channel.TextChannel):
            self.bot.db.execute("UPDATE channel SET guild_id = %s, category_id = %s, name = %s, position = %s WHERE id = %s", (after.guild.id, after.category_id, after.name, after.position, after.id))

        elif isinstance(after, discord.channel.CategoryChannel):
            self.bot.db.execute("UPDATE category SET guild_id = %s, name = %s, position = %s WHERE id = %s", (after.guild.id, after.id, after.name, after.position, after.id))

        self.bot.db.commit()

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if not self.bot.db.connect():
            return

        if isinstance(channel, discord.channel.TextChannel):
            self.bot.db.execute("UPDATE channel SET deleted = true WHERE id = %s", (channel.id,))

        elif isinstance(channel, discord.channel.CategoryChannel):
            self.bot.db.execute("UPDATE category SET deleted = true WHERE id = %s", (channel.id,))

        self.bot.db.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not self.bot.db.connect():
            return

        self.bot.db.execute("INSERT INTO `member` (id, name, avatar_url) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE id=id", (member.id, member.name, str(member.avatar_url)))
        self.bot.db.commit()

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if not self.bot.db.connect():
            return

        self.bot.db.execute("UPDATE `member` SET name = %s, avatar_url = %s WHERE id = %s", (after.name, str(after.avatar_url), after.id))
        self.bot.db.commit()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not self.bot.db.connect():
            return

        self.bot.db.execute("UPDATE member SET deleted = true WHERE id = %s", (member.id,))
        self.bot.db.commit()


def setup(bot):
    bot.add_cog(Logger(bot))
    print("Cog loaded: Logger")
