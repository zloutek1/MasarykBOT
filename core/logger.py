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
        """
        name: usually a cog name,
        task_get: a function to format the data for database input
        task_insert: a function that inserts data into database
        """
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
        # assert row exists
        await self.db.execute("""
            INSERT INTO logger (state)
            SELECT * FROM (SELECT 'failed') AS tmp
            WHERE NOT EXISTS (
                SELECT * FROM logger
            ) LIMIT 1;
        """)

        # set state to 'failed' and time to NOW()
        await self.db.execute("""
            UPDATE logger SET to_date=NOW() WHERE state='failed';
            UPDATE logger SET from_date=to_date, to_date=NOW() WHERE state='success';
            UPDATE logger SET state='failed', finished_at=NULL;
        """)
        await self.db.commit()

        # get process row
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

        try:
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
        except discord.errors.Forbidden:
            pass

    """--------------------------------------------------------------------------------------------------------------------------"""

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

    """--------------------------------------------------------------------------------------------------------------------------"""

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

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_message(self, message):
        message_data = (message.channel.id, message.author.id, message.id, message.content, message.created_at)
        await self.db.execute("""
            INSERT INTO message
                (channel_id, author_id, id, content, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE id=id
        """, message_data)
        await self.db.commit()

    @commands.Cog.listener()
    @needs_database
    async def on_raw_message_edit(self, payload):
        message_data = (payload.data.get("content", ""), payload.data["channel_id"], payload.data["id"])
        await self.db.execute("""
            UPDATE message
            SET content = %s
            WHERE channel_id = %s AND id = %s
        """, message_data)
        await self.db.commit()

    @commands.Cog.listener()
    @needs_database
    async def on_raw_message_delete(self, payload):
        message_data = (payload.channel_id, payload.message_id)
        await self.db.execute("""
            UPDATE message
            SET deleted_at = NOW()
            WHERE channel_id = %s AND id = %s
        """, message_data)
        await self.db.commit()


    @commands.Cog.listener()
    @needs_database
    async def on_raw_bulk_message_delete(self, payload):
        messages_data = [(payload.channel_id, message_id)
                         for message_id in payload.message_ids]
        await self.db.executemany("""
            UPDATE message
            SET deleted_at = NOW()
            WHERE channel_id = %s AND id = %s
        """, messages_data)
        await self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_guild_join(self, guild):
        guild_data = (guild.id, guild.name, str(guild.icon_url))
        await self.db.execute("""
            INSERT INTO guild (id, name, icon_url)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE id=id
        """, guild_data)
        await self.db.commit()

    @commands.Cog.listener()
    @needs_database
    async def on_guild_update(self, before, after):
        guild_data = (before.id, before.name, str(before.icon_url),
                      after.id, after.name, str(after.icon_url))
        await self.db.execute("""
            UPDATE guild
            SET id=%s, name=%s, icon_url=%s
            WHERE id=%s AND name=%s AND icon_url=%s
        """, guild_data)
        await self.db.commit()

    @commands.Cog.listener()
    @needs_database
    async def on_guild_remove(self, guild):
        guild_data = (guild.id, guild.name)
        await self.db.execute("""
            UPDATE guild
            SET deleted_at=NOW()
            WHERE id=%s AND name=%s
        """, guild_data)
        await self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_guild_channel_create(self, channel):
        if isinstance(channel, discord.CategoryChannel):
            await on_category_create(channel)

        elif isinstance(channel, discord.TextChannel):
            await on_text_channel_create(channel)

    @needs_database
    async def on_category_create(self, category):
        category_data = (category.guild.id, category.id, category.name, category.position)
        await self.db.execute("""
            INSERT INTO category (guild_id, id, name, position)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE id=id
        """, category_data)
        await self.db.commit()

    @needs_database
    async def on_text_channel_create(self, text_channel):
        channel_data = (text_channel.guild.id, text_channel.category_id, text_channel.id, text_channel.name, text_channel.position)
        await self.db.executemany("""
            INSERT INTO channel (guild_id, category_id, id, name, position)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE id=id
        """, channel_data)
        await self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_guild_channel_update(self, before, after):
        if isinstance(after, discord.CategoryChannel):
            await on_category_update(before, after)

        elif isinstance(after, discord.TextChannel):
            await on_text_channel_update(before, after)

    @needs_database
    async def on_category_update(self, before, after):
        category_data = (before.guild.id, before.id, before.name, before.position, after.guild.id, after.id, after.name, after.position)
        await self.db.execute("""
            UPDATE category
            SET guild_id=%s, id=%s, name=%s, position=%s
            WHERE guild_id=%s AND id=%s AND name=%s AND position=%s
        """, category_data)
        await self.db.commit()

    @needs_database
    async def on_text_channel_update(self, before, after):
        channel_data = (before.guild.id, before.category_id, before.id, before.name, before.position,
            after.guild.id, after.category_id, after.id, after.name, after.position)
        await self.db.executemany("""
            UPDATE channel
            SET guild_id=%s, category_id=%s, id=%s, name=%s, position=%s
            WHERE guild_id=%s AND category_id=%s AND id=%s AND name=%s AND position=%s
        """, channel_data)
        await self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_guild_channel_delete(self, channel):
        if isinstance(channel, discord.CategoryChannel):
            await on_category_delete(channel)

        elif isinstance(channel, discord.TextChannel):
            await on_text_channel_delete(channel)

    @needs_database
    async def on_category_delete(self, category):
        category_data = (category.guild.id, category.id)
        await self.db.execute("""
            UPDATE category
            SET deleted_at=NOW()
            WHERE guild_id=%s AND id=%s
        """, category_data)
        await self.db.commit()

    @needs_database
    async def on_text_channel_delete(self, text_channel):
        channel_data = (text_channel.guild.id, text_channel.id)
        await self.db.executemany("""
            UPDATE channel
            SET deleted_at=NOW()
            WHERE guild_id=%s AND id=%s
        """, channel_data)
        await self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_member_join(self, member):
        member_data = (member.id, member.name, str(member.avatar_url))
        await self.db.executemany("""
            INSERT INTO `member` (id, name, avatar_url)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE id=id
        """, member_data)
        await self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_user_update(self, before, after):
        member_data = (before.id, before.name, str(before.avatar_url),
                       after.id, after.name, str(after.avatar_url))
        await self.db.executemany("""
            UPDATE `member`
            SET id=%s, name=%s, avatar_url=%s
            WHERE id=%s AND name=%s AND avatar_url=%s
        """, member_data)
        await self.db.commit()

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_member_remove(self, member):
        member_data = (member.id,)
        await self.db.executemany("""
            UPDATE `member`
            SET deleted_at=NOW()
            WHERE id=%s
        """, member_data)
        await self.db.commit()



def setup(bot):
    bot.add_cog(Logger(bot))
