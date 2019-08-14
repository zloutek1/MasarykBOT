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

    def add_catchup_task(self, name, task_get, task_insert):
        self.catchup_tasks.setdefault(name, [])
        self.catchup_tasks[name].append({
            "get": task_get,
            "insert": task_insert,
            "data": []})

    """--------------------------------------------------------------------------------------------------------------------------"""

    @staticmethod
    def chunks(l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    """--------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def backup_guilds(self, guilds):
        guilds_data = [(g.id, g.name, str(g.icon_url))
                       for g in guilds]

        chunks = self.chunks(guilds_data, 550)
        for chunk in chunks:
            await self.db.executemany("""
                INSERT INTO guild (id, name, icon_url)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id""", chunk)
        await self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def backup_categories(self, categories):
        category_data = [(c.guild.id, c.id, c.name, c.position)
                         for c in categories]

        chunks = self.chunks(category_data, 550)
        for chunk in chunks:
            await self.db.executemany("""
                INSERT INTO category (guild_id, id, name, position)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id""", chunk)
        await self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def backup_text_channels(self, text_channels):
        channels_data = [(c.guild.id, c.category_id, c.id, c.name, c.position)
                         for c in text_channels]

        chunks = self.chunks(channels_data, 550)
        for chunk in chunks:
            await self.db.executemany("""
                INSERT INTO channel (guild_id, category_id, id, name, position)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id""", chunk)
        await self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def backup_users(self, users):
        users_data = [(u.id, u.name, str(u.avatar_url))
                      for u in users]

        chunks = self.chunks(users_data, 550)
        for chunk in chunks:
            await self.db.executemany("""
                INSERT INTO `member` (id, name, avatar_url)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id""", chunk)
        await self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def backup_messages(self, in_channels):
        await self.db.execute("""
            UPDATE logger SET to_date=NOW() WHERE state='failed';
            UPDATE logger SET from_date=to_date, to_date=NOW() WHERE state='success';
            UPDATE logger SET state='failed', finished_at=NULL;
        """)
        await self.db.commit()

        await self.db.execute("SELECT * FROM logger")
        row = await self.db.fetchone()

        ##
        # backup messages for each channel
        ##
        for i, channel in enumerate(in_channels):
            print("    [Logger] Backing up messages in", channel, f"({i} / {len(in_channels)})")

            authors_data = set()
            messages_data = []
            attachments_data = []

            await self.get_messages(channel, authors_data, messages_data, attachments_data, after=row["from_date"], before=row["to_date"])

            await self.backup_users(list(authors_data))
            await self.backup_messages_in(channel, messages_data)
            await self.backup_attachments_in(channel, attachments_data)

            for task_name in self.catchup_tasks:
                for catchup_task in self.catchup_tasks[task_name]:
                    catchup_task_insert = catchup_task["insert"]
                    await catchup_task_insert(catchup_task["data"])
                    catchup_task["data"].clear()

        await self.db.execute("UPDATE logger SET state='success', finished_at=NOW() WHERE state='failed'")
        await self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def get_messages(self, channel, authors_data, messages_data, attachments_data, after=None, before=None):

        async for message in channel.history(
                limit=1_000_000, after=after, before=before, oldest_first=True):

            # -- Author --
            authors_data.add(message.author)

            # -- Message --
            messages_data += [(message.channel.id, message.author.id, message.id, message.content, message.created_at)]

            # -- Attachment --
            attachments_data += [(message.id, a.id, a.filename, a.url)
                                 for a in message.attachments]

            # -- Other catching up tasks --
            for task_name in self.catchup_tasks:
                for catchup_task in self.catchup_tasks[task_name]:
                    catchup_task_get = catchup_task["get"]
                    await catchup_task_get(message, catchup_task["data"])

    @needs_database
    async def backup_messages_in(self, channel, messages_data):
        chunks = self.chunks(messages_data, 550)
        for chunk in chunks:
            await self.db.executemany("""
                INSERT INTO message
                    (channel_id, author_id, id, content, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id""", chunk)
        await self.db.commit()

    @needs_database
    async def backup_attachments_in(self, channel, attachments_data):
        chunks = self.chunks(attachments_data, 550)
        for chunk in chunks:
            await self.db.executemany("""
                INSERT INTO attachment
                    (message_id, id, filename, url)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id""", chunk)
        await self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_ready(self):
        self.bot.readyCogs[self.__class__.__name__] = False

        guilds = self.bot.guilds
        categories = [c for guild in guilds for c in guild.categories]
        text_channels = [c for guild in guilds for c in guild.text_channels]
        users = [m for guild in guilds for m in guild.members]

        print("    [Logger] Begining backup")
        await self.backup_guilds(guilds)
        await self.backup_categories(categories)
        await self.backup_text_channels(text_channels)
        await self.backup_users(users)
        print("    [Logger] Backed up guilds, categories, text_channels, users\n")

        await self.backup_messages(in_channels=text_channels)
        print("    [Logger] Backed up messages")

        self.bot.readyCogs[self.__class__.__name__] = True


def setup(bot):
    bot.add_cog(Logger(bot))
