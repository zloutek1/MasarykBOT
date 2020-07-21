from discord import Member
from discord.abc import PrivateChannel
from discord.ext import tasks, commands

import asyncio
import logging
from datetime import timedelta, datetime

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

        for guild in self.bot.guilds:
            await self.synchronize_categories_in(guild)
            await self.synchronize_channels_in(guild)
            await self.synchronize_members_in(guild)
            await self.synchronize_roles_in(guild)

            await self.backup_messages_in(guild)

        log.info("backup process finished")

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
            INSERT INTO server.guilds AS g (id, name, icon_url, created_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE
                SET name=$2,
                    icon_url=$3,
                    created_at=$4,
                    edited_at=NOW()
                WHERE g.name<>excluded.name OR
                      g.icon_url<>excluded.icon_url OR
                      g.created_at<>excluded.created_at
        """, data)

        log.info(f"backed up {len(data)} guilds")

    @acquire_conn
    async def synchronize_categories_in(self, guild, conn):
        data = [(guild.id, category.id, category.name, category.position, category.created_at) for category in guild.categories]
        await conn.executemany("""
            INSERT INTO server.categories AS c (guild_id, id, name, position, created_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE
                SET name=$3,
                    position=$4,
                    created_at=$5,
                    edited_at=NOW()
                WHERE c.name<>excluded.name OR
                      c.position<>excluded.position OR
                      c.created_at<>excluded.created_at
        """, data)

        log.info(f"backed up {len(data)} categories")

    @acquire_conn
    async def synchronize_channels_in(self, guild, conn):
        data = [(guild.id, channel.category.id if channel.category is not None else None, channel.id, channel.name, channel.position, channel.created_at) for channel in guild.text_channels]
        await conn.executemany("""
            INSERT INTO server.channels AS ch (guild_id, category_id, id, name, position, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO UPDATE
                SET name=$4,
                    position=$5,
                    created_at=$6,
                    edited_at=NOW()
                WHERE ch.name<>excluded.name OR
                      ch.position<>excluded.position OR
                      ch.created_at<>excluded.created_at
        """, data)

        log.info(f"backed up {len(data)} text_channels")

    @acquire_conn
    async def synchronize_members_in(self, guild, conn):
        data = [(member.id, member.name, str(member.avatar_url), member.created_at) for member in guild.members]

        await conn.executemany("""
            INSERT INTO server.users AS u (id, names, avatar_url, created_at)
            VALUES ($1, ARRAY[$2], $3, $4)
            ON CONFLICT (id) DO UPDATE
                SET names=array_prepend($2::varchar, u.names),
                    avatar_url=$3,
                    created_at=$4,
                    edited_at=NOW()
                WHERE $2<>ANY(u.names) OR
                      u.avatar_url<>excluded.avatar_url OR
                      u.created_at<>excluded.created_at
        """, data)

        log.info(f"backed up {len(data)} members")

    @acquire_conn
    async def synchronize_roles_in(self, guild, conn):
        data = [(guild.id, role.id, role.name, hex(role.color.value), role.created_at) for role in guild.roles]

        await conn.executemany("""
            INSERT INTO server.roles AS r (guild_id, id, name, color, created_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE
                SET name=$3,
                    color=$4,
                    created_at=$5,
                    edited_at=NOW()
                WHERE r.name<>excluded.name OR
                      r.color<>excluded.color OR
                      r.created_at<>excluded.created_at
        """, data)

        log.info(f"backed up {len(data)} roles")

    @acquire_conn
    async def backup_messages_in(self, guild, conn):
        row = await conn.fetchrow("SELECT * FROM cogs.logger WHERE guild_id = $1 LIMIT 1", guild.id)

        if row is None:
            from_date = guild.created_at
            to_date = from_date + timedelta(weeks=1)

            await self.backup_between(from_date, to_date, guild=guild, conn=conn)

            await conn.execute("""
                INSERT INTO cogs.logger (guild_id, from_date, to_date, finished_at)
                VALUES ($1, $2, $3, now())
            """, guild.id, from_date, to_date)

            log.info(f"backed up first attempt between {from_date} and {to_date} in {guild}")

        else:
            failed_rows = await conn.fetch("""
                SELECT *
                FROM cogs.logger
                WHERE guild_id = $1 AND finished_at IS NULL
            """, guild.id)

            for row in failed_rows:
                from_date = row.get("from_date")
                to_date = row.get("to_date")

                await self.backup_between(from_date, to_date, guild=guild, conn=conn)

                await conn.execute("""
                    UPDATE cogs.logger
                    SET finished_at = now()
                    WHERE guild_id=$1 AND from_date=$2 AND to_date=$3
                """, guild.id, from_date, to_date)

                log.info(f"backed up ex-failed attempt between {from_date} and {to_date} in {guild}")

        latest_row = await conn.fetchrow("SELECT * FROM cogs.logger WHERE guild_id = $1 ORDER BY to_date DESC", guild.id)
        from_date = latest_row.get("to_date")
        while from_date < datetime.now():
            to_date = from_date + timedelta(weeks=1)

            await self.backup_between(from_date, to_date, guild=guild, conn=conn)

            await conn.execute("""
                INSERT INTO cogs.logger (guild_id, from_date, to_date, finished_at)
                VALUES ($1, $2, $3, now())
            """, guild.id, from_date, to_date)

            log.info(f"backed up new section between {from_date} and {to_date} in {guild}")

            await asyncio.sleep(5)
            from_date = to_date

        log.info(f"Backed up messages in {guild}")

    async def backup_between(self, from_date, to_date, guild, conn):
        for i, channel in enumerate(guild.text_channels):
            attachments = []
            messages = []
            authors = set()

            async for message in channel.history(after=from_date, before=to_date, limit=None, oldest_first=True):
                author = message.author
                authors.add((author.id, author.name, str(author.avatar_url), author.created_at))

                messages.append((message.channel.id, message.author.id, message.id, message.content, message.created_at, message.edited_at))

                for attachment in message.attachments:
                    attachments.append((message.id, attachment.id, attachment.filename, attachment.url))

            else:
                await conn.executemany("""
                    INSERT INTO server.users AS u (id, names, avatar_url, created_at)
                    VALUES ($1, ARRAY[$2], $3, $4)
                    ON CONFLICT (id) DO NOTHING
                """, authors)

                await conn.executemany("""
                    INSERT INTO server.messages AS m (channel_id, author_id, id, content, created_at, edited_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id) DO UPDATE
                        SET content=$4,
                            created_at=$5,
                            edited_at=$6
                        WHERE m.content<>excluded.content OR
                              m.created_at<>excluded.created_at OR
                              m.edited_at<>excluded.edited_at""", messages)

                await conn.executemany("""
                    INSERT INTO server.attachments AS a (message_id, id, filename, url)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO UPDATE
                        SET filename=$3,
                            url=$4
                        WHERE a.filename<>excluded.filename OR
                              a.url<>excluded.url""", attachments)

                log.debug(f"Backed up {len(messages)} messages in #{channel}, {guild} ({i} / {len(guild.text_channels)})")


def setup(bot):
    bot.add_cog(Logger(bot))
