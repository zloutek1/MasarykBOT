from discord import Member
from discord.abc import PrivateChannel
from discord.ext import tasks, commands

import logging
from datetime import timedelta

log = logging.getLogger(__name__)


def acquire_conn(func):
    async def wrapper(self, *args, **kwargs):
        conn = await self.pool.acquire()
        try:
            return await func(self, *args, **kwargs, conn=conn)
        finally:
            await self.pool.release(conn)
    return wrapper


class Logger(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @property
    def pool(self):
        return self.bot.pool

    @commands.Cog.listener()
    async def on_ready(self):
        await self.run_backup()

    @tasks.loop(hours=2.0)
    async def repeat_backup(self):
        await self.run_backup()

    @commands.command()
    async def backup(self, ctx):
        await self.run_backup()

    async def run_backup(self):
        await self.synchronize_guilds()
        await self.synchronize_categories()
        await self.synchronize_channels()
        await self.synchronize_members()
        await self.synchronize_roles()

        #for guild in self.bot.guilds:
        #    await self.backup_in(guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        log.info(f"joined guild {guild.name}")
        # TODO

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        log.info(f"updated guild from {before.name} to {after.name}")
        # TODO

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        log.info(f"left guild {guild.name}")

    @commands.Cog.listener()
    async def on_channel_create(self, channel):
        if isinstance(channel, PrivateChannel):
            return

        # TODO

    @commands.Cog.listener()
    async def on_channel_update(self, before, after):
        if isinstance(before, PrivateChannel):
            return

        # TODO

    @commands.Cog.listener()
    async def on_channel_delete(self, channel):
        if isinstance(channel, PrivateChannel):
            return

        # TODO

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, PrivateChannel):
            return

        if not isinstance(message.author, Member):
            return

        # TODO

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if isinstance(before.channel, PrivateChannel):
            return

        # TODO

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if isinstance(message.channel, PrivateChannel):
            return

        # TODO

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild

        # TODO

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        guild = after.guild

        # TODO

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild

        # TODO

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        pass

        # TODO

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        pass

        # TODO

    @commands.Cog.listener()
    async def on_guild_role_remove(self, role):
        pass

        # TODO

    @acquire_conn
    async def synchronize_guilds(self, conn):
        data = [(guild.id, guild.name, str(guild.icon_url), guild.created_at) for guild in self.bot.guilds]
        await conn.executemany("""
            INSERT INTO server.guilds (id, name, icon_url, created_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE
                SET name=$2, icon_url=$3, created_at=$4, edited_at=NOW()
                WHERE excluded.name<>$2 OR excluded.icon_url<>$3 OR excluded.created_at<>$4""", data)

        log.info(f"backed up {len(data)} guilds")

    @acquire_conn
    async def synchronize_categories(self, conn):
        data = [(guild.id, category.id, category.name, category.position, category.created_at) for guild in self.bot.guilds for category in guild.categories]
        await conn.executemany("""
            INSERT INTO server.categories (guild_id, id, name, position, created_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE
                SET name=$3, position=$4, created_at=$5, edited_at=NOW()
                WHERE excluded.name<>$3 OR excluded.position<>$4 OR excluded.created_at<>$5""", data)

        log.info(f"backed up {len(data)} categories")

    @acquire_conn
    async def synchronize_channels(self, conn):
        data = [(guild.id, channel.category.id if channel.category is not None else None, channel.id, channel.name, channel.position, channel.created_at) for guild in self.bot.guilds for channel in guild.text_channels]
        await conn.executemany("""
            INSERT INTO server.channels (guild_id, category_id, id, name, position, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO UPDATE
                SET name=$4, position=$5, created_at=$6, edited_at=NOW()
                WHERE excluded.name<>$4 OR excluded.position<>$5 OR excluded.created_at<>$6""", data)

        log.info(f"backed up {len(data)} text_channels")

    @acquire_conn
    async def synchronize_members(self, conn):
        data = [(member.id, member.name, str(member.avatar_url), member.created_at) for guild in self.bot.guilds for member in guild.members]

        await conn.executemany("""
            INSERT INTO server.users (id, names, avatar_url, created_at)
            VALUES ($1, ARRAY[$2], $3, $4)
            ON CONFLICT (id) DO UPDATE
                SET names=array_prepend($2::varchar, server.users.names), avatar_url=$3, created_at=$4, edited_at=NOW()
                WHERE $2<>ANY(server.users.names) OR excluded.avatar_url<>$3 OR excluded.created_at<>$4""", data)

        log.info(f"backed up {len(data)} members")

    @acquire_conn
    async def synchronize_roles(self, conn):
        data = [(guild.id, role.id, role.name, hex(role.color.value), role.created_at) for guild in self.bot.guilds for role in guild.roles]

        await conn.executemany("""
            INSERT INTO server.roles (guild_id, id, name, color, created_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE
                SET name=$3, color=$4, created_at=$5, edited_at=NOW()
                WHERE excluded.name<>$3 OR excluded.color<>$4 OR excluded.created_at<>$5""", data)

        log.info(f"backed up {len(data)} roles")

    async def backup_in(self, guild):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM cogs.logger WHERE guild_id = $1", guild.id)
            if len(rows) == 0:
                from_date = guild.created_at
                to_date = from_date + timedelta(weeks=1)

                await self.backup_between(from_date, to_date, guild=guild, conn=conn)
                return

            for row in rows:
                from_date = row.get("from_date")
                to_date = row.get("to_date")

                await self.backup_between(from_date, to_date, guild=guild, conn=conn)

    async def backup_between(self, from_date, to_date, guild, conn):
        for i, channel in enumerate(guild.text_channels):
            attachments = []
            messages = []

            async for message in channel.history(after=from_date, before=to_date, limit=None, oldest_first=True):
                messages.append((message.channel.id, message.author.id, message.id, message.content, message.created_at, message.edited_at))

                for attachment in message.attachments:
                    attachments.append((message.id, attachment.id, attachment.filename, attachment.url))
            else:
                await conn.executemany("INSERT INTO server.messages VALUES ($1, $2, $3, $4, $5, $6)", messages)
                await conn.executemany("INSERT INTO server.attachments VALUES ($1, $2, $3, $4)", attachments)

                log.debug(f"Backed up {len(messages)} messages in #{channel}, {guild} ({i} / {len(guild.text_channels)})")


def setup(bot):
    bot.add_cog(Logger(bot))
