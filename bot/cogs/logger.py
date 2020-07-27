from discord import Member, TextChannel, CategoryChannel
from discord.abc import PrivateChannel
from discord.ext import tasks, commands
from discord.errors import Forbidden

import re
import emoji
import asyncio
import logging
from itertools import islice
from collections import deque, Counter
from datetime import datetime, timedelta

from bot.cogs.utils.checks import acquire_conn
from bot.cogs.utils import schemas

log = logging.getLogger(__name__)


async def prepare_guild(guild):
    return (guild.id, guild.name, str(guild.icon_url), guild.created_at)


async def prepare_category(category):
    return (category.guild.id, category.id, category.name, category.position, category.created_at)


async def prepare_role(role):
    return (role.guild.id, role.id, role.name, hex(role.color.value), role.created_at)


async def prepare_member(member):
    return (member.id, member.name, str(member.avatar_url), member.created_at)


async def prepare_channel(channel):
    category_id = channel.category.id if channel.category is not None else None
    return (channel.guild.id, category_id, channel.id, channel.name, channel.position, channel.created_at)


async def prepare_message(message):
    return (message.channel.id, message.author.id, message.id, message.content, message.created_at, message.edited_at)


async def prepare_attachment(message, attachment):
    return (message.id, attachment.id, attachment.filename, attachment.url)


async def prepare_reaction(reaction):
    user_ids = await reaction.users().map(lambda member: member.id).flatten()
    emote = reaction.emoji if isinstance(reaction.emoji, str) else reaction.emoji.name
    return (reaction.message.id, emoji.demojize(emote), reaction.count, user_ids)

###
#
###
#
###


class Logger(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.message_insert_queue = deque()
        self.message_delete_queue = deque()
        self.member_update_queue = deque()

        self.message_insert_queued.start()
        self.message_delete_queued.start()
        self.member_update_queued.start()

    @property
    def pool(self):
        return self.bot.pool

    ###
    #
    ###
    #
    ###

    @tasks.loop(minutes=1)
    @acquire_conn
    async def message_insert_queued(self, conn):
        if not self.message_insert_queue:
            return

        first_500 = [self.message_insert_queue.popleft()
                     for _ in range(min(500, len(self.message_insert_queue)))]
        await conn.executemany(schemas.SQL_INSERT_MESSAGE, first_500)
        log.debug(f"inserted {len(first_500)} messages to database")

    @tasks.loop(minutes=1)
    @acquire_conn
    async def message_delete_queued(self, conn):
        if not self.message_delete_queue:
            return

        first_500 = [self.message_delete_queue.popleft()
                     for _ in range(min(500, len(self.message_delete_queue)))]
        await conn.executemany("UPDATE server.messages SET deleted_at = NOW() WHERE id = $1", first_500)
        log.debug(f"deleted {len(first_500)} messages from database")

    @tasks.loop(minutes=1)
    @acquire_conn
    async def member_update_queued(self, conn):
        if not self.member_update_queue:
            return

        first_500 = [self.member_update_queue.popleft()
                     for _ in range(min(500, len(self.member_update_queue)))]
        await conn.executemany(schemas.SQL_INSERT_USER, first_500)
        log.debug(f"inserted {len(first_500)} members to database")

    ###
    #
    ###
    #
    ###

    async def backup(self):
        log.info("Starting backup process")
        await self.backup_guilds()

        for guild in self.bot.guilds:
            await self.backup_categories(guild)
            await self.backup_roles(guild)
            await self.backup_members(guild)
            await self.backup_channels(guild)

        log.info("Finished backup process")

    @acquire_conn
    async def backup_guilds(self, conn):
        data = [await prepare_guild(guild) for guild in self.bot.guilds]
        await conn.executemany(schemas.SQL_INSERT_GUILD, data)

    @acquire_conn
    async def backup_categories(self, guild, conn):
        data = [await prepare_category(category) for category in guild.categories]
        await conn.executemany(schemas.SQL_INSERT_CATEGORY, data)

    @acquire_conn
    async def backup_roles(self, guild, conn):
        data = [await prepare_role(role) for role in guild.roles]
        await conn.executemany(schemas.SQL_INSERT_ROLE, data)

    @acquire_conn
    async def backup_members(self, guild, conn):
        data = [await prepare_member(member) for member in guild.members]
        await conn.executemany(schemas.SQL_INSERT_USER, data)

    @acquire_conn
    async def backup_channels(self, guild, conn):
        data = [await prepare_channel(channel) for channel in guild.text_channels]
        await conn.executemany(schemas.SQL_INSERT_CHANNEL, data)

        while (failed := await self.backup_failed_week(guild)):
            log.debug("finished running failed process, re-checking if everything is fine...")
            await asyncio.sleep(2)

        while (still_begind := await self.backup_new_week(guild)):
            log.debug("newer week exists, re-running backup for next week")
            await asyncio.sleep(2)

        log.debug(f"finished backing up messages for {guild}")

    @acquire_conn
    async def backup_failed_week(self, guild, conn):
        failed_row = await conn.fetchrow("SELECT * FROM cogs.logger WHERE guild_id = $1 AND finished_at IS NULL", guild.id)
        row = await conn.fetchrow("SELECT * FROM cogs.logger WHERE guild_id = $1 AND finished_at IS NOT NULL", guild.id)

        if failed_row is not None:
            from_date = failed_row.get("from_date")
            to_date = failed_row.get("to_date")

            for channel in guild.text_channels:
                await self.backup_messages(channel, from_date, to_date)

            await self.backup_mark_finished(guild, row, from_date, to_date)

        return failed_row is not None

    @acquire_conn
    async def backup_mark_finished(self, guild, row, from_date, to_date, conn):
        if row is None:
            await conn.execute("UPDATE cogs.logger SET finished_at = NOW() WHERE guild_id = $1 AND finished_at IS NULL", guild.id)
        else:
            async with conn.transaction():
                await conn.execute("DELETE FROM cogs.logger WHERE guild_id = $1 AND from_date = $2 AND to_date = $3", guild.id, from_date, to_date)
                await conn.execute("UPDATE cogs.logger SET to_date = $3, finished_at = NOW() WHERE guild_id = $1 AND to_date = $2 AND finished_at IS NOT NULL", guild.id, from_date, to_date)

    @acquire_conn
    async def backup_new_week(self, guild, conn):
        row = await conn.fetchrow("SELECT * FROM cogs.logger WHERE guild_id = $1", guild.id)

        if row is None:
            from_date = guild.created_at
            to_date = from_date + timedelta(weeks=1)
        else:
            from_date = row.get("to_date")
            to_date = row.get("to_date") + timedelta(weeks=1)

        await conn.execute("INSERT INTO cogs.logger VALUES ($1, $2, $3, NULL)", guild.id, from_date, to_date)

        for channel in guild.text_channels:
            await self.backup_messages(channel, from_date, to_date)

        await self.backup_mark_finished(guild, row, from_date, to_date)

        return to_date + timedelta(weeks=1) < datetime.now()

    @acquire_conn
    async def backup_messages(self, channel, from_date, to_date, conn):
        if channel.last_message_id is None:
            return

        try:
            log.debug(f"backing up messages {from_date.strftime('%d.%m.%Y')} - {to_date.strftime('%d.%m.%Y')} in {channel} ({channel.guild})")
            authors, messages, attachments, reactions, emojis = [], [], [], [], []

            async for message in channel.history(after=from_date, before=to_date, oldest_first=True):
                authors.append(await prepare_member(message.author))

                messages.append(await prepare_message(message))

                attachments.extend([await prepare_attachment(message, attachment)
                                    for attachment in message.attachments])

                reactions.extend([await prepare_reaction(reaction)
                                  for reaction in message.reactions])

                emojis.extend([(message.id, emote, count)
                               for emote, count in (await self.get_emojis(message)).items()])

            await conn.executemany(schemas.SQL_INSERT_USER, authors)
            await conn.executemany(schemas.SQL_INSERT_MESSAGE, messages)
            await conn.executemany(schemas.SQL_INSERT_ATTACHEMNT, attachments)
            await conn.executemany(schemas.SQL_INSERT_REACTIONS, reactions)
            await conn.executemany(schemas.SQL_INSERT_EMOJIS, emojis)
        except Forbidden:
            log.debug(f"missing permissions to backup messages in {channel} ({channel.guild})")

    async def get_emojis(self, message):
        REGEX = r"((?::\w+(?:~\d+)?:)|(?:<\d+:\w+:>))"
        emojis = re.findall(REGEX, emoji.demojize(message.content))
        return Counter(emojis)

    ###
    #
    ###
    #
    ###

    @commands.Cog.listener()
    async def on_ready(self):
        await self.backup()

    @tasks.loop(hours=168)  # 168 hours == 1 week
    async def _repeat_backup(self):
        await self.backup()

    @commands.command(name="backup")
    async def _backup(self, ctx):
        await self.backup()

    @commands.Cog.listener()
    @acquire_conn
    async def on_guild_join(self, guild, conn):
        log.info(f"joined guild {guild}")
        data = await prepare_guild(guild)
        await conn.execute(schemas.SQL_INSERT_GUILD, *data)

    @commands.Cog.listener()
    @acquire_conn
    async def on_guild_update(self, before, after, conn):
        log.info(f"updated guild from {before} to {after}")
        data = await prepare_guild(after)
        await conn.execute(schemas.SQL_INSERT_GUILD, *data)

    @commands.Cog.listener()
    @acquire_conn
    async def on_guild_remove(self, guild, conn):
        log.info(f"left guild {guild}")
        await conn.execute("UPDATE server.guilds SET deleted_at=NOW() WHERE id = $1;", guild.id)

    @commands.Cog.listener()
    @acquire_conn
    async def on_guild_channel_create(self, channel, conn):
        log.info(f"created channel {channel}")

        if isinstance(channel, TextChannel):
            data = await prepare_channel(channel)
            await conn.execute(schemas.SQL_INSERT_CHANNEL, *data)

        elif isinstance(channel, CategoryChannel):
            data = await prepare_category(channel)
            await conn.execute(schemas.SQL_INSERT_CATEGORY, *data)

    @commands.Cog.listener()
    @acquire_conn
    async def on_guild_channel_update(self, before, after, conn):
        log.info(f"updated channel {before}")

        if isinstance(channel, TextChannel):
            data = await prepare_channel(after)
            await conn.execute(schemas.SQL_INSERT_CHANNEL, *data)

        elif isinstance(channel, CategoryChannel):
            data = await prepare_category(after)
            await conn.execute(schemas.SQL_INSERT_CATEGORY, *data)

    @commands.Cog.listener()
    @acquire_conn
    async def on_guild_channel_delete(self, channel, conn):
        if isinstance(channel, PrivateChannel):
            return

        log.info(f"deleted channel {channel}")

        if isinstance(channel, TextChannel):
            await conn.execute("UPDATE server.channels SET deleted_at=NOW() WHERE id = $1;", channel.id)

        elif isinstance(channel, CategoryChannel):
            await conn.execute("UPDATE server.categories SET deleted_at=NOW() WHERE id = $1;", channel.id)

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, PrivateChannel):
            return

        if not isinstance(message.author, Member):
            return

        self.message_insert_queue.append(await prepare_message(message))

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if isinstance(before.channel, PrivateChannel):
            return

        self.message_insert_queue.append(await prepare_message(after))

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if isinstance(message.channel, PrivateChannel):
            return

        self.message_delete_queue.append((message.id,))

    @commands.Cog.listener()
    @acquire_conn
    async def on_member_join(self, member, conn):
        log.info(f"member {member} joined")

        data = await prepare_member(member)
        await conn.execute(schemas.SQL_INSERT_USER, *data)

    @commands.Cog.listener()
    @acquire_conn
    async def on_member_update(self, before, after, conn):
        if before.avatar_url != after.avatar_url:
            log.info(f"member {before} updated his avatar_url")
        elif before.name != after.name:
            log.info(f"member {before} ({before.nick}) updated his name to {after}")
        elif before.nick != after.nick:
            log.info(f"member {before} ({before.nick}) updated his nickname to {after.nick}")
        else:
            return

        self.member_update_queue.append(await prepare_member(after))

    @commands.Cog.listener()
    @acquire_conn
    async def on_member_remove(self, member, conn):
        log.info(f"member {member} left")

        await conn.execute("UPDATE server.users SET deleted_at=NOW() WHERE id = $1", member.id)

    @commands.Cog.listener()
    @acquire_conn
    async def on_guild_role_create(self, role, conn):
        log.info(f"added role {role}")

        data = await prepare_role(role)
        await conn.execute(schemas.SQL_INSERT_ROLE, *data)

    @commands.Cog.listener()
    @acquire_conn
    async def on_guild_role_update(self, before, after, conn):
        log.info(f"updated role from {before} to {after}")

        data = await prepare_role(after)
        await conn.execute(schemas.SQL_INSERT_ROLE, *data)

    @commands.Cog.listener()
    @acquire_conn
    async def on_guild_role_remove(self, role, conn):
        log.info(f"removed role{role}")

        await conn.execute("UPDATE server.roles SET deleted_at=NOW() WHERE id = $1", role.id)


def setup(bot):
    bot.add_cog(Logger(bot))
