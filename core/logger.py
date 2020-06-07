import logging

import discord
from discord.ext import tasks, commands

import json
from datetime import timedelta

from core.utils.db import Database
from core.utils.checks import needs_database, safe


class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger(__name__)

        self.bot.add_catchup_task = self.add_catchup_task
        self.catchup_tasks = {}

        self.printer.start()

    """--------------------------------------------------------------------------------------------------------------------------"""

    def add_catchup_task(self, name, task_get, task_insert, task_data=[]):
        """
        add catchup_task to self.catchup_tasks

        @param name: usually a cog name,
        @param task_get: a function to format the data for database input
        @param task_insert: a function that inserts data into database
        """
        self.catchup_tasks[name] = {
            "get": task_get,
            "insert": task_insert,
            "data": task_data
        }

    """--------------------------------------------------------------------------------------------------------------------------"""

    @staticmethod
    def chunks(l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    """--------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def backup_guilds(self, guilds, db: Database = None):
        """
        save guilds in format
            (id, name, icon_url)
        into database in chunks
        """

        guilds_data = [(g.id, g.name, str(g.icon_url))
                       for g in guilds]

        chunks = self.chunks(guilds_data, 550)
        for chunk in chunks:
            await db.executemany("""
                INSERT INTO guild (id, name, icon_url)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id""", chunk)
            await db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def backup_categories(self, categories, db: Database = None):
        """
        save categories in format
            (guild_id, id, name, position)
        into database in chunks
        """

        category_data = [(c.guild.id, c.id, c.name, c.position)
                         for c in categories]

        chunks = self.chunks(category_data, 550)
        for chunk in chunks:
            await db.executemany("""
                INSERT INTO category (guild_id, id, name, position)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id""", chunk)
            await db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def backup_text_channels(self, text_channels, db: Database = None):
        """
        save text_channels in format
            (guild_id, category_id, id, name, position)
        into database in chunks
        """

        channels_data = [(c.guild.id, c.category_id, c.id, c.name, c.position)
                         for c in text_channels]

        chunks = self.chunks(channels_data, 550)
        for chunk in chunks:
            await db.executemany("""
                INSERT INTO channel (guild_id, category_id, id, name, position)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id""", chunk)
            await db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def backup_users(self, users, db: Database = None):
        """
        save users in format
            (id, name, avarar_url)
        into database in chunks
        """

        users_data = [(u.id, u.name, str(u.avatar_url))
                      for u in users]

        chunks = self.chunks(users_data, 550)
        for chunk in chunks:
            await db.executemany("""
                INSERT INTO `member` (id, name, avatar_url)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id""", chunk)
            await db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @staticmethod
    def last_day_of_month(any_day):
        next_month = any_day.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)

    @staticmethod
    def prev_month(any_day):
        first_day = any_day.replace(day=1)
        return first_day - timedelta(days=1)

    @needs_database
    async def backup_messages(self, in_channels, db: Database = None):
        """
        start backing up messages in_channel
        get from_date, to_date ranges from
        table logger from database

        for each channel
            skip the channel if it has no messages
            get the message objects using get_messages method
            backup the messages using backup_messages
            backup also catchup_tasks

        if everything went smoothly set logger status as 'success'
        """

        # assert row exists
        await db.execute("""
            INSERT INTO logger (state)
            SELECT * FROM (SELECT 'failed') AS tmp
            WHERE NOT EXISTS (
                SELECT * FROM logger
            ) LIMIT 1;
        """)

        # set state to 'failed' and time to NOW()
        await db.execute("""
            UPDATE logger SET to_date=NOW() WHERE state='failed';
            UPDATE logger SET from_date=to_date, to_date=NOW() WHERE state='success';
            UPDATE logger SET state='failed', finished_at=NULL;
        """)
        await db.commit()

        # get process row
        await db.execute("SELECT * FROM logger")
        row = await db.fetchone()

        ##
        # backup messages for each channel
        ##
        for i, channel in enumerate(in_channels):
            if not channel.last_message_id:
                self.log.info(f"Skipping channel {channel} ({i} / {len(in_channels)})")
                continue

            self.log.info(f"Backing up messages in {channel} ({i} / {len(in_channels)})")

            authors_data = set()
            messages_data = []
            attachments_data = []

            after = (None
                     if row["from_date"] is None else
                     row["from_date"].replace(day=1)
                     if row["from_date"].day > 1 else
                     self.prev_month(row["from_date"]).replace(day=1))
            before = (None
                      if row["to_date"] else
                      self.last_day_of_month(row["to_date"]))

            await safe(self.get_messages)(channel, authors_data, messages_data, attachments_data, after=after, before=before)

            await self.backup_users(list(authors_data))
            await self.backup_messages_in(channel, messages_data)
            await self.backup_attachments_in(channel, attachments_data)

            for task_name in self.catchup_tasks:
                self.log.info(f"Running catchup task named {task_name}")
                catchup_task = self.catchup_tasks[task_name]

                catchup_task_insert = catchup_task["insert"]
                await catchup_task_insert(catchup_task["data"])
                catchup_task["data"].clear()

        await db.execute("UPDATE logger SET state='success', finished_at=NOW() WHERE state='failed'")
        await db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def get_messages(self, channel, authors_data, messages_data, attachments_data, after=None, before=None, db: Database = None):
        """
        log the last 1 milion messages
        save message in format
            (channel_id, author_id, id, content, created_at)

        save all attachemnts in format
            (message_id, id, filename, url)

        call catchup_task.get for each catchup_task
        """

        try:
            counter = 0
            async for message in channel.history(
                    limit=1_000_000, after=after, before=before, oldest_first=True):

                # -- Author --
                authors_data.add(message.author)

                # -- Message --
                messages_data += [(message.channel.id, message.author.id,
                                   message.id, message.content, message.created_at)]

                # -- Attachment --
                attachments_data += [(message.id, a.id, a.filename, a.url)
                                     for a in message.attachments]

                # -- Other catching up tasks --
                for task_name in self.catchup_tasks:
                    catchup_task = self.catchup_tasks[task_name]

                    catchup_task_get = catchup_task["get"]
                    await catchup_task_get(message, catchup_task["data"])

                if counter % 1000 == 0 and counter != 0:
                    self.log.info(
                        f"Stored {counter} messages in {channel.name}")

                counter += 1
        except discord.errors.Forbidden:
            pass

    """--------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def backup_messages_in(self, channel, messages_data, db: Database = None):
        """
        save messages in format
            (channel_id, author_id, id, content, created_at)
        into database in chunks
        """

        chunks = self.chunks(messages_data, 550)
        for i, chunk in enumerate(chunks):
            await db.executemany("""
                INSERT INTO message
                    (channel_id, author_id, id, content, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id""", chunk)
            await db.commit()
            self.log.info(
                f"Saved {(i + 1) * 550} messages in {channel.name} to database")

    """--------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def backup_attachments_in(self, channel, attachments_data, db: Database = None):
        """
        save attachments in format
            (message_id, id, filename, url)
        into database in chunks
        """

        chunks = self.chunks(attachments_data, 550)
        for chunk in chunks:
            await db.executemany("""
                INSERT INTO attachment
                    (message_id, id, filename, url)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id""", chunk)
        await db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_ready(self, db: Database = None):
        """
        start backing up everything necessary
        - guilds
        - categories
        - text channels
        - users
        - messages
        """

        self.bot.readyCogs[self.__class__.__name__] = False

        guilds = self.bot.guilds
        categories = [c for guild in guilds for c in guild.categories]
        text_channels = [c for guild in guilds for c in guild.text_channels]
        users = [m for guild in guilds for m in guild.members]

        self.log.info("Begining backup")
        await self.backup_guilds(guilds)
        await self.backup_categories(categories)
        await self.backup_text_channels(text_channels)
        await self.backup_users(users)
        self.log.info("Backed up guilds, categories, text_channels, users\n")

        await self.backup_messages(in_channels=text_channels)
        self.log.info("Backed up messages")

        self.bot.readyCogs[self.__class__.__name__] = True

    """--------------------------------------------------------------------------------------------------------------------------"""

    @tasks.loop(hours=2.0)
    async def printer(self):
        await self.bot.wait_until_ready()

        if all(self.bot.readyCogs.values()) or len(self.bot.readyCogs.values()) == 0:
            await self.bot.trigger_event("on_ready")

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_guild_channel_create(self, channel, db: Database = None):
        """
        determine if channel is text_channel or a category
        """

        if isinstance(channel, discord.CategoryChannel):
            await self.backup_categories([channel])

        elif isinstance(channel, discord.TextChannel):
            await self.backup_text_channels([channel])

    """--------------------------------------------------------------------------------------------------------------------------"""


def setup(bot):
    bot.add_cog(Logger(bot))
