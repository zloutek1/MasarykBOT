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

        self.bot.add_catchup_task = self.add_catchup_task
        self.catchup_tasks = {}

    """--------------------------------------------------------------------------------------------------------------------------"""

    def add_catchup_task(self, name, task):
        self.catchup_tasks.setdefault(name, [])
        self.catchup_tasks[name].append(task)

    """--------------------------------------------------------------------------------------------------------------------------"""

    async def log_messages(self, channel, since, message_data, attachment_data):
        until = datetime.now()

        if not channel.last_message_id:
            return

        try:
            async for message in channel.history(limit=10000, after=since, before=until, oldest_first=True):

                # -- Message --
                message_data += [(message.channel.id, message.author.id, message.id, message.content, message.created_at)]

                # insert into SQL
                if len(message_data) > 100:
                    await self.messages_insert(message_data)
                    message_data.clear()

                # -- Attachment --
                for attachment in message.attachments:
                    attachment_data += [(message.id, attachment.id, attachment.filename, attachment.url)]

                    # insert into SQL
                    if len(attachment_data) > 100:
                        await self.attachment_insert(attachment_data)
                        attachment_data.clear()

                # -- Other catching up tasks --
                for task_name in self.catchup_tasks:
                    for catchup_task in self.catchup_tasks[task_name]:
                        await catchup_task(message)

        except discord.Forbidden:
            pass

        except discord.errors.NotFound:
            pass

    """--------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def messages_insert(self, message_data):
        self.db.executemany("INSERT IGNORE INTO message (channel_id, author_id, id, content, created_at) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE content=content", message_data)
        self.db.commit()

    @needs_database
    async def attachment_insert(self, attachment_data):
        self.db.executemany("INSERT IGNORE INTO attachment (message_id, id, filename, url) VALUES (%s, %s, %s, %s)", attachment_data)
        self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_ready(self):
        self.bot.readyCogs[self.__class__.__name__] = False

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
        self.db.executemany("INSERT INTO guild (id, name, icon_url) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE name=name", guild_data)
        self.db.executemany("INSERT INTO category (guild_id, id, name, position) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE name=name", category_data)
        self.db.executemany("INSERT INTO channel (guild_id, category_id, id, name, position) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE name=name", channel_data)
        self.db.executemany("INSERT INTO `member` (id, name, avatar_url) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE name=name", member_data)
        self.db.commit()

        # console print
        print("    [Logger] Updated database for: guilds, categories, channels, members")
        print()

        # get SQL data
        message_data = []
        attachment_data = []

        # get last send message time in each channel
        self.db.execute("SELECT channel_id, MAX(created_at) AS created_at FROM (SELECT * FROM `message` WHERE 1) AS res1 GROUP BY channel_id")
        rows = self.db.fetchall()

        # insert messages into database
        for i, channel in enumerate(channels):
            row = core.utils.get(rows, channel_id=channel.id)
            since = None

            if row:
                since = row["created_at"]
                since += timedelta(seconds=1)

            padding = " " * (max(map(lambda ch: len(ch.name), channels)) - len(channel.name))
            print("\r    [Logger] Updating database for {}. {}/{}".format(channel, i + 1, len(channels)) + padding, end="")

            await self.log_messages(channel, since, message_data, attachment_data)
        print()

        # insert leftovers
        if len(message_data) > 0:
            await self.messages_insert(message_data)
        if len(attachment_data) > 0:
            await self.attachment_insert(attachment_data)

        # console print
        values_for = [
            "messages",
            "attachemnts",
            ", ".join(
                task_name
                for task_name in self.catchup_tasks)
        ]
        print("    [Logger] Updated database for:", ", ".join(values_for))
        print()

        self.bot.readyCogs[self.__class__.__name__] = True

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_message(self, message):
        message_data = [(message.channel.id, message.author.id, message.id, message.content, message.created_at)]
        await self.messages_insert(message_data)

        attachment_data = [(message.id, attachment.id, attachment.filename, attachment.url) for attachment in message.attachments]
        await self.attachment_insert(attachment_data)

        for task_name in self.catchup_tasks:
            for catchup_task in self.catchup_tasks[task_name]:
                await catchup_task(message)

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_raw_message_delete(self, payload):

        self.db.execute("UPDATE message SET deleted = true WHERE id = %s", (payload.message_id,))
        self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_guild_join(self, guild):

        self.db.execute("INSERT INTO guild (id, name, icon_url) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE name=name", (guild.id, guild.name, str(guild.icon_url)))
        self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_guild_update(self, before, after):

        self.db.execute("UPDATE guild SET name = %s, icon_url = %s WHERE id = %s", (after.name, str(after.icon_url), after.id))
        self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_guild_remove(self, guild):

        self.db.execute("UPDATE guild SET deleted = true WHERE id = %s", (guild.id,))
        self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_guild_channel_create(self, channel):

        if isinstance(channel, discord.channel.TextChannel):
            self.db.execute("INSERT INTO channel (guild_id, category_id, id, name, position) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE name=name", (channel.guild.id, channel.category_id, channel.id, channel.name, channel.position))
            self.db.commit()

        elif isinstance(channel, discord.channel.CategoryChannel):
            self.db.execute("INSERT INTO category (guild_id, id, name, position) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE name=name", (channel.guild.id, channel.id, channel.name, channel.position))
            self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_guild_channel_update(self, before, after):

        if isinstance(after, discord.channel.TextChannel):
            self.db.execute("UPDATE channel SET guild_id = %s, category_id = %s, name = %s, position = %s WHERE id = %s", (after.guild.id, after.category_id, after.name, after.position, after.id))

        elif isinstance(after, discord.channel.CategoryChannel):
            self.db.execute("UPDATE category SET guild_id = %s, name = %s, position = %s WHERE id = %s", (after.guild.id, after.name, after.position, after.id))

        self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_guild_channel_delete(self, channel):

        if isinstance(channel, discord.channel.TextChannel):
            self.db.execute("UPDATE channel SET deleted = true WHERE id = %s", (channel.id,))

        elif isinstance(channel, discord.channel.CategoryChannel):
            self.db.execute("UPDATE category SET deleted = true WHERE id = %s", (channel.id,))

        self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_member_join(self, member):

        self.db.execute("INSERT INTO `member` (id, name, avatar_url) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE name=name", (member.id, member.name, str(member.avatar_url)))
        self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_user_update(self, before, after):

        self.db.execute("UPDATE `member` SET name = %s, avatar_url = %s WHERE id = %s", (after.name, str(after.avatar_url), after.id))
        self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_member_remove(self, member):

        self.db.execute("UPDATE member SET deleted = true WHERE id = %s", (member.id,))
        self.db.commit()


def setup(bot):
    bot.add_cog(Logger(bot))
