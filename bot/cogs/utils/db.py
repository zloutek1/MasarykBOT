import asyncio
import asyncpg
import logging

import re
from emoji import demojize, get_emoji_regexp
from functools import wraps
from datetime import datetime, timezone
from collections import Counter
from abc import ABC, abstractmethod

from discord import Guild, CategoryChannel, Role, Member, TextChannel, Message, Attachment, Reaction, Emoji, PartialEmoji
from typing import List, Tuple, TypeVar, Generic, Union
Record = asyncpg.Record
T = TypeVar('T')
AnyEmote = Union[Emoji, PartialEmoji, str]


log = logging.getLogger(__name__)


def withConn(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        async with self.pool.acquire() as conn:
            return await func(self, conn, *args, **kwargs)
    return wrapper

class Table:
    def __init__(self, pool):
        self.pool = pool

    @withConn
    async def select(self, conn, data):
        raise NotImplementedError("select not implemented for this table")

    @withConn
    async def insert(self, conn, data):
        raise NotImplementedError("insert not implemented for this table")

    @withConn
    async def update(self, conn, data):
        raise NotImplementedError("update not implemented for this table")

    @withConn
    async def delete(self, conn, data):
        raise NotImplementedError("hard delete not implemented for this table, perhaps try soft delete?")

    @withConn
    async def soft_delete(self, conn, data):
        raise NotImplementedError("soft delete not implemented for this table, perhaps try hard delete?")



class Mapper(ABC, Generic[T]):
    @staticmethod
    @abstractmethod
    async def prepare_one(obj: T):
        raise NotImplementedError("prepare_one form object not implemented for this table")

    @abstractmethod
    async def prepare(self, objs: List[T]):
        raise NotImplementedError("prepare form objects not implemented for this table")



class FromMessageMapper(ABC):
    @abstractmethod
    async def prepare_from_message(self, objs: Message):
        raise NotImplementedError("prepare_from_message form objects not implemented for this table")



class Guilds(Table, Mapper[Guild]):
    @staticmethod
    async def prepare_one(guild: Guild):
        return (guild.id, guild.name, str(guild.icon_url), guild.created_at)

    async def prepare(self, guilds: List[Guild]):
        return [await self.prepare_one(guild) for guild in guilds]

    @withConn
    async def select(self, conn, guild_id):
        return await conn.fetch("""
            SELECT * FROM server.guilds WHERE id=$1
        """, guild_id)

    @withConn
    async def insert(self, conn, data):
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

    @withConn
    async def update(self, conn, data):
        await self.insert.__wrapped__(self, conn, data)

    @withConn
    async def soft_delete(self, conn, ids):
        await conn.executemany("UPDATE server.guilds SET deleted_at=NOW() WHERE id = $1;", ids)



class Categories(Table, Mapper[CategoryChannel]):
    @staticmethod
    async def prepare_one(category: CategoryChannel):
        return (category.guild.id, category.id, category.name, category.position, category.created_at)

    async def prepare(self, categories: List[CategoryChannel]):
        return [await self.prepare_one(category) for category in categories]

    @withConn
    async def select(self, conn, category_id):
        return await conn.fetch("""
            SELECT * FROM server.categories WHERE id=$1
        """, category_id)

    @withConn
    async def insert(self, conn, data):
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

    @withConn
    async def update(self, conn, data):
        await self.insert.__wrapped__(self, conn, data)

    @withConn
    async def soft_delete(self, conn, ids):
        await conn.executemany("UPDATE server.categories SET deleted_at=NOW() WHERE id = $1;", ids)



class Roles(Table, Mapper[Role]):
    @staticmethod
    async def prepare_one(role: Role):
        return (role.guild.id, role.id, role.name, hex(role.color.value), role.created_at)

    async def prepare(self, roles: List[Role]):
        return [await self.prepare_one(role) for role in roles]

    @withConn
    async def select(self, conn, role_id):
        return await conn.fetch("""
            SELECT * FROM server.roles WHERE id=$1
        """, role_id)

    @withConn
    async def insert(self, conn, data):
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

    @withConn
    async def update(self, conn, data):
        await self.insert.__wrapped__(self, conn, data)

    @withConn
    async def soft_delete(self, conn, ids):
        await conn.executemany("UPDATE server.roles SET deleted_at=NOW() WHERE id = $1;", ids)



class Members(Table, Mapper[Member], FromMessageMapper):
    @staticmethod
    async def prepare_one(member: Member):
        return (member.id, member.name, str(member.avatar_url), member.created_at)

    async def prepare(self, members: List[Member]):
        return [await self.prepare_one(member) for member in members]

    async def prepare_from_message(self, message):
        return [await self.prepare_one(message.author)]

    @withConn
    async def select(self, conn, user_id):
        return await conn.fetch("""
            SELECT * FROM server.users WHERE id=$1
        """, user_id)

    @withConn
    async def insert(self, conn, data):
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

    @withConn
    async def update(self, conn, data):
        await self.insert.__wrapped__(self, conn, data)

    @withConn
    async def soft_delete(self, conn, ids):
        await conn.executemany("UPDATE server.users SET deleted_at=NOW() WHERE id = $1;", ids)



class Channels(Table, Mapper[TextChannel]):
    @staticmethod
    async def prepare_one(channel: TextChannel):
        category_id = channel.category.id if channel.category is not None else None
        return (channel.guild.id, category_id, channel.id, channel.name, channel.position, channel.created_at)

    async def prepare(self, channels: List[TextChannel]):
        return [await self.prepare_one(channel) for channel in channels]

    @withConn
    async def select(self, conn, channel_id):
        return await conn.fetch("""
            SELECT * FROM server.channels WHERE id=$1
        """, channel_id)

    @withConn
    async def insert(self, conn, data):
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

    @withConn
    async def update(self, conn, data):
        await self.insert.__wrapped__(self, conn, data)

    @withConn
    async def soft_delete(self, conn, ids):
        await conn.executemany("UPDATE server.channels SET deleted_at=NOW() WHERE id = $1;", ids)



class Messages(Table, Mapper[Message]):
    @staticmethod
    async def prepare_one(message: Message):
        return (message.channel.id, message.author.id, message.id, message.content, message.created_at)

    async def prepare(self, messages: List[Message]):
        return [await self.prepare_one(message) for message in messages]

    @withConn
    async def select(self, conn, message_id):
        return await conn.fetch("""
            SELECT * FROM server.messages WHERE id=$1
        """, message_id)

    @withConn
    async def insert(self, conn, messages):
        await conn.executemany("""
            INSERT INTO server.messages AS m (channel_id, author_id, id, content, created_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE
                SET content=$4,
                    created_at=$5,
                    edited_at=NOW()
                WHERE m.content<>excluded.content OR
                        m.created_at<>excluded.created_at OR
                        m.edited_at<>excluded.edited_at
        """, messages)

    @withConn
    async def update(self, conn, messages):
        await self.insert.__wrapped__(self, conn, messages)

    @withConn
    async def soft_delete(self, conn, ids):
        await conn.executemany("UPDATE server.messages SET deleted_at=NOW() WHERE id = $1;", ids)



class Attachments(Table, Mapper[Attachment], FromMessageMapper):
    @staticmethod
    async def prepare_one(attachment: Attachment):
        return (attachment.id, attachment.filename, attachment.url)

    async def prepare(self, attachments: List[Attachment]):
        return [await self.prepare_one(attachment) for attachment in attachments]

    async def prepare_from_message(self, message: Message):
        return [(message.id, attachment_id, filename, url)
                for (attachment_id, filename, url) in await self.prepare(message.attachments)
               ]

    @withConn
    async def select(self, conn, attachment_id):
        return await conn.fetch("""
            SELECT * FROM server.attachments WHERE id=$1
        """, attachment_id)

    @withConn
    async def insert(self, conn, data):
        await conn.executemany("""
            INSERT INTO server.attachments AS a (message_id, id, filename, url)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE
                SET filename=$3,
                    url=$4
                WHERE a.filename<>excluded.filename OR
                        a.url<>excluded.url
        """, data)



class Emojis(Table, Mapper[AnyEmote], FromMessageMapper):
    HAS_EMOTE = r":[\w~]+:"
    REGULAR_REGEX = r"<:([\w~]+):(\d+)>"
    ANIMATED_REGEX = r"<a:([\w~]+):(\d+)>"

    @staticmethod
    async def prepare_one(emoji: AnyEmote):
        if isinstance(emoji, str):
            return await Emojis.prepare_unicode_emoji(emoji)
        return (emoji.id, emoji.name, str(emoji.url), emoji.animated)

    @staticmethod
    async def prepare_unicode_emoji(emoji: str):
        emoji_id = sum(map(ord, emoji))
        hex_id = '_'.join(hex(ord(char))[2:] for char in emoji)
        url = "https://unicode.org/emoji/charts/full-emoji-list.html#{hex}".format(hex=hex_id)
        return (emoji_id, demojize(emoji).strip(':'), url, False)

    async def prepare(self, emojis: List[AnyEmote]):
        return [await self.prepare_one(emoji) for emoji in emojis]

    @staticmethod
    def to_url(emoji_id: int, *, animated: bool=False):
        return f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if animated else 'png'}"

    async def _prepare_emojis_from_message(self, message: Message, regex: str, *, is_animated: bool):
        emojis = re.findall(regex, message.content)
        return [(int(emoji_id), emoji_name, self.to_url(int(emoji_id), animated=is_animated), is_animated)
                for (emoji_name, emoji_id) in emojis]

    async def _prepare_from_message_content(self, message: Message):
        if not re.search(self.HAS_EMOTE, demojize(message.content)):
            return []

        regular_emojis = await self._prepare_emojis_from_message(message, self.REGULAR_REGEX, is_animated=False)
        animated_emojis = await self._prepare_emojis_from_message(message, self.ANIMATED_REGEX, is_animated=True)
        unicode_emojis = [await Emojis.prepare_unicode_emoji(emoji)
                          for emoji in get_emoji_regexp().findall(message.content)]

        return regular_emojis + animated_emojis + unicode_emojis

    async def _prepare_from_message_reactions(self, message: Message):
        return [await self.prepare_one(reaction.emoji)
                for reaction in message.reactions]

    async def prepare_from_message(self, message: Message):
        return (await self._prepare_from_message_content(message)
               + await self._prepare_from_message_reactions(message))

    @withConn
    async def select(self, conn, emoji_id):
        return await conn.fetch("""
            SELECT * FROM server.emojis WHERE id=$1
        """, emoji_id)

    @withConn
    async def insert(self, conn, data):
        await conn.executemany("""
            INSERT INTO server.emojis AS e (id, name, url, animated)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE
                SET name=$2,
                    url=$3,
                    animated=$4,
                    edited_at=NOW()
                WHERE e.name<>excluded.name OR
                      e.url<>excluded.url OR
                      e.animated<>excluded.animated
        """, data)

    @withConn
    async def update(self, conn, data):
        await self.insert.__wrapped__(self, conn, data)

    @withConn
    async def soft_delete(self, conn, ids):
        await conn.executemany("UPDATE server.emojis SET deleted_at=NOW() WHERE id = $1;", ids)


class MessageEmojis(Table, FromMessageMapper):
    def __init__(self, pool):
        super().__init__(pool)
        self.emojis = Emojis(self.pool)

    async def prepare_from_message(self, message: Message):
        emojis = await self.emojis._prepare_from_message_content(message)
        emoji_ids = [emoji[0] for emoji in emojis]
        return [(message.id, emoji_id, count) for (emoji_id, count) in Counter(emoji_ids).items()]

    @withConn
    async def select(self, conn, emoji_id):
        return await conn.fetch("""
            SELECT * FROM server.message_emojis WHERE message_id=$1 AND emoji_id=$2
        """, emoji_id)

    @withConn
    async def insert(self, conn, data):
        await conn.executemany("""
            INSERT INTO server.message_emojis AS me (message_id, emoji_id, count)
            VALUES ($1, $2, $3)
            ON CONFLICT (message_id, emoji_id) DO UPDATE
                SET count=$3,
                    edited_at=NOW()
                WHERE me.count<>excluded.count
        """, data)

    @withConn
    async def update(self, conn, data):
        await self.insert.__wrapped__(self, conn, data)


class Reactions(Table, Mapper[Reaction], FromMessageMapper):
    @staticmethod
    async def prepare_one(reaction: Reaction):
        user_ids = (await reaction.users()
                                  .map(lambda member: member.id)
                                  .flatten())
        emoji_id = (emote.id
                    if isinstance(emote := reaction.emoji, (Emoji, PartialEmoji)) else
                    sum(map(ord, emote)))

        return (reaction.message.id, emoji_id, user_ids, reaction.message.created_at)

    async def prepare(self, reactions: List[Reaction]):
        return [await self.prepare_one(reaction) for reaction in reactions]

    async def prepare_from_message(self, message: Message):
        return await self.prepare(message.reactions)

    @withConn
    async def select(self, conn, message_id, emoji_id):
        return await conn.fetch("""
            SELECT * FROM server.reactions WHERE message_id=$1 AND emoji_id=$2
        """, message_id, emoji_id)

    @withConn
    async def insert(self, conn, reactions):
        await conn.executemany("""
            INSERT INTO server.reactions AS r (message_id, emoji_id, member_ids, created_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (message_id, emoji_id) DO UPDATE
                SET member_ids=$3,
                    created_at=$4,
                    edited_at=NOW()
                WHERE r.member_ids<>excluded.member_ids OR
                      r.created_at<>excluded.created_at
        """, reactions)

    @withConn
    async def update(self, conn, reactions):
        await self.insert.__wrapped__(self, conn, reactions)

    @withConn
    async def soft_delete(self, conn, ids):
        await conn.executemany("UPDATE server.reactions SET deleted_at=NOW() WHERE message_id = $1 AND emoji_id=$2;", ids)


class Logger(Table):
    @withConn
    async def select(self, conn, channel_id):
        return await conn.fetch("SELECT * FROM cogs.logger WHERE channel_id = $1", channel_id)

    @withConn
    async def start_process(self, conn, channel_id, from_date, to_date):
        await conn.execute("""
            INSERT INTO cogs.logger VALUES ($1, $2, $3, NULL)
            ON CONFLICT (channel_id, from_date) DO NOTHING
        """, channel_id, from_date, to_date)

    @withConn
    async def mark_process_finished(self, conn, channel_id, from_date, to_date, is_first_week=False):
        if is_first_week:
            await conn.execute("UPDATE cogs.logger SET finished_at = NOW() WHERE channel_id = $1 AND finished_at IS NULL", channel_id)
        else:
            async with conn.transaction():
                await conn.execute("DELETE FROM cogs.logger WHERE channel_id = $1 AND from_date = $2 AND to_date = $3", channel_id, from_date, to_date)
                await conn.execute("UPDATE cogs.logger SET to_date = $3, finished_at = NOW() WHERE channel_id = $1 AND to_date = $2 AND finished_at IS NOT NULL", channel_id, from_date, to_date)

    def process(self, channel_id, from_date, to_date, is_first_week=False, conn=None):
        return self.Process(self, channel_id, from_date, to_date, is_first_week, conn)

    class Process:
        def __init__(self, cls, guild_id, from_date, to_date, is_first_week=False, conn=None):
            self.parent = cls
            self.conn = conn

            self.guild_id = guild_id
            self.from_date = from_date
            self.to_date = to_date
            self.is_first_week = is_first_week

        async def __aenter__(self):
            if self.conn:
                return await self.parent.start_process.__wrapped__(self.parent, self.conn, self.guild_id, self.from_date, self.to_date)
            return await self.parent.start_process(self.guild_id, self.from_date, self.to_date)

        async def __aexit__(self, exc_type, exc, tb):
            if self.conn:
                await self.parent.mark_process_finished.__wrapped__(self.parent, self.conn, self.guild_id, self.from_date, self.to_date, self.is_first_week)
            await self.parent.mark_process_finished(self.guild_id, self.from_date, self.to_date, self.is_first_week)


class Leaderboard(Table):
    @withConn
    async def preselect(self, conn, guild_id, ignored_users, channel_id):
        await conn.execute("DROP TABLE IF EXISTS ldb_lookup")
        await conn.execute("""
            CREATE TEMPORARY TABLE IF NOT EXISTS ldb_lookup AS
                SELECT
                    ROW_NUMBER() OVER (ORDER BY sent_total DESC), *
                FROM (
                    SELECT
                        author_id,
                        author.names[1] AS author,
                        SUM(messages_sent) AS sent_total
                    FROM cogs.leaderboard
                    INNER JOIN server.users AS author
                        ON author_id = author.id
                    INNER JOIN server.channels AS channel
                        ON channel_id = channel.id
                    WHERE guild_id = $1::bigint AND
                            author_id<>ALL($2::bigint[]) AND
                            ($3::bigint IS NULL OR channel_id = $3)
                    GROUP BY author_id, author.names
                    ORDER BY sent_total DESC
                ) AS lookup
        """, guild_id, ignored_users, channel_id)

    @withConn
    async def get_top10(self, conn):
        return await conn.fetch("SELECT * FROM ldb_lookup LIMIT 10")

    @withConn
    async def get_around(self, conn, author_id):
        return await conn.fetch("""
            WITH desired_count AS (
                SELECT sent_total
                FROM ldb_lookup
                WHERE author_id = $1
            )

            (   SELECT *
                FROM ldb_lookup
                WHERE sent_total >= (SELECT * FROM desired_count) AND author_id <> $1
                ORDER BY sent_total LIMIT 2
            ) UNION (
                SELECT *
                FROM ldb_lookup
                WHERE sent_total = (SELECT * FROM desired_count) AND author_id = $1 LIMIT 1
            ) UNION (
                SELECT *
                FROM ldb_lookup
                WHERE sent_total < (SELECT * FROM desired_count) AND author_id <> $1 LIMIT 2
            ) ORDER BY sent_total DESC
        """, author_id)



class Emojiboard(Table):
    @withConn
    async def select(self, conn, guild_id, ignored_users, channel_id, author_id, emoji_id):
        return await conn.fetch("""
            SELECT
                emoji.name,
                SUM(count) AS sent_total
            FROM cogs.emojiboard
            INNER JOIN server.channels AS channel
                ON channel_id = channel.id
            INNER JOIN server.emojis AS emoji
                ON emoji_id = emoji.id
            WHERE guild_id = $1::bigint AND
                    author_id<>ALL($2::bigint[]) AND
                    ($3::bigint IS NULL OR channel_id = $3) AND
                    ($4::bigint IS NULL OR author_id = $4) AND
                    ($5::bigint IS NULL OR emoji_id = $5)
            GROUP BY emoji.name
            ORDER BY sent_total DESC
            LIMIT 10
        """, guild_id, ignored_users, channel_id, author_id, emoji_id)



class Subjects(Table):
    @withConn
    async def find(self, conn, code, faculty="FI"):
        return await conn.fetch("SELECT * FROM muni.subjects WHERE LOWER(code) LIKE LOWER($1) AND LOWER(faculty) = LOWER($2)", code, faculty)

    @withConn
    async def find_registered(self, conn, guild_id, code, faculty="FI"):
        return await conn.fetchrow("""
            SELECT * FROM muni.registers
            WHERE guild_id = $1 AND LOWER(code) LIKE LOWER($2) AND LOWER(faculty) = LOWER($3)""", guild_id, code, faculty)

    @withConn
    async def find_serverinfo(self, conn, guild_id, code, faculty="FI"):
        return await conn.fetchrow("""
            SELECT * FROM muni.subject_server
            WHERE guild_id = $1 AND LOWER(code) LIKE LOWER($2) AND LOWER(faculty) = LOWER($3)""", guild_id, code, faculty)

    @withConn
    async def find_users_subjects(self, conn, guild_id, member_id):
        return await conn.fetch("""
            SELECT * FROM muni.registers
            WHERE guild_id = $1 AND $2::bigint = ANY(member_ids)
        """, guild_id, member_id)

    @withConn
    async def sign_user(self, conn, guild_id, code, member_id, faculty="FI"):
        await conn.execute("""
            INSERT INTO muni.registers AS r (guild_id, faculty, code, member_ids)
                    VALUES ($1, $2, $3, ARRAY[$4::bigint])
            ON CONFLICT (guild_id, code) DO UPDATE
                SET member_ids = array_append(r.member_ids, $4::bigint)
                WHERE $4::bigint <> ALL(r.member_ids);
        """, guild_id, faculty, code, member_id)

    @withConn
    async def unsign_user(self, conn, guild_id, code, member_id, faculty="FI"):
        await conn.execute("""
            UPDATE muni.registers
                SET member_ids = array_remove(member_ids, $4::bigint)
                WHERE guild_id = $1 AND
                        LOWER(faculty) = LOWER($2) AND
                        LOWER(code) = LOWER($3) AND
                        $4 = ANY(member_ids);
        """, guild_id, faculty, code, member_id)

    @withConn
    async def unsign_user_from_all(self, conn, guild_id, member_id):
        await conn.execute("""
            UPDATE muni.registers
                SET member_ids = array_remove(member_ids, $2::bigint)
                WHERE guild_id = $1 AND
                      $2::bigint = ANY(member_ids)
        """, guild_id, member_id)

    @withConn
    async def get_category(self, conn, guild_id, code, faculty="FI"):
        return await conn.fetchrow(
            "SELECT * FROM muni.subject_category WHERE LOWER(faculty) = LOWER($1) AND LOWER(code) LIKE LOWER($2) AND guild_id = $3",
            faculty, code, guild_id)

    @withConn
    async def set_channel(self, conn, guild_id, code, channel_id, faculty="FI"):
        await conn.execute("""
            INSERT INTO muni.subject_server AS ss (guild_id, faculty, code, channel_id)
                    VALUES ($1, $2, $3, $4)
            ON CONFLICT (guild_id, faculty, code) DO UPDATE
                SET channel_id = excluded.channel_id
                WHERE ss.channel_id IS NULL OR ss.channel_id <> excluded.channel_id;
        """, guild_id, faculty, code, channel_id)

    @withConn
    async def set_category(self, conn, guild_id, code, category_id, faculty="FI"):
        await conn.execute("""
            UPDATE muni.subject_server
                SET category_id = $4
                WHERE guild_id = $1 AND LOWER(faculty) = LOWER($2) AND LOWER(code) LIKE LOWER($3);
        """, guild_id, faculty, code, category_id)

    @withConn
    async def remove_channel(self, conn, guild_id, code, faculty="FI"):
        await conn.execute("""
            DELETE FROM muni.subject_server
                WHERE guild_id = $1 AND
                        LOWER(faculty) = LOWER($2) AND
                        LOWER(code) = LOWER($3)
        """, guild_id, faculty, code)

class Seasons(Table):
    @withConn
    async def load_events(self, conn, guild_id):
        return await conn.fetch("""
            SELECT * FROM cogs.seasons
            WHERE guild_id = $1 AND
                  from_date IS NOT NULL AND
                  to_date IS NOT NULL
            ORDER BY to_date ASC, from_date DESC
        """, guild_id)

    @withConn
    async def find(self, conn, guild_id, id):
        return await conn.fetchrow("""
            SELECT * FROM cogs.seasons
            WHERE guild_id = $1 AND
                  id = $2 AND
                  from_date IS NOT NULL AND
                  to_date IS NOT NULL
            ORDER BY to_date ASC, from_date DESC
        """, guild_id, id)

    @withConn
    async def load_current_event(self, conn, guild_id):
        return await conn.fetchrow("""
            SELECT * FROM cogs.seasons
            WHERE guild_id = $1 AND
                  from_date < NOW() AND
                  NOW() < to_date
		 	ORDER BY (to_date - from_date)
        """, guild_id)

    @withConn
    async def load_default_event(self, conn, guild_id):
        return await conn.fetchrow("""
            SELECT * FROM cogs.seasons
            WHERE guild_id = $1 AND
                  name = 'default'
        """, guild_id)

    @withConn
    async def insert(self, conn, events):
        await conn.executemany("""
            INSERT INTO cogs.seasons AS s (guild_id, name, from_date, to_date, icon, banner)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (guild_id, name) DO UPDATE
                SET icon = excluded.icon,
                    banner = excluded.banner
        """, events)

    @withConn
    async def update(self, conn, guild_id, icon, banner):
        await conn.execute("""
            UPDATE cogs.seasons
            SET icon = $2,
                banner = $3
            WHERE guild_id = $1
        """, guild_id, icon, banner)

    @withConn
    async def delete(self, conn, guild_id, id):
        await conn.execute("""
            DELETE FROM cogs.seasons
            WHERE guild_id = $1 AND id = $2
        """, guild_id, id)

class DBBase:
    def __init__(self, pool):
        self.pool = pool

    @classmethod
    def connect(cls, url):
        try:
            loop = asyncio.get_event_loop()
            pool = loop.run_until_complete(asyncpg.create_pool(url, command_timeout=1280))
            return Database(pool)
        except OSError as e:
            import re
            redacted_url = re.sub(r'\:(?!\/\/)[^\@]+', ":******", url)
            log.error("Failed to connect to database (%s)", redacted_url)
            raise e



class Database(DBBase):
    def __init__(self, *args):
        super().__init__(*args)

        self.guilds = Guilds(self.pool)
        self.categories = Categories(self.pool)
        self.roles = Roles(self.pool)
        self.members = Members(self.pool)
        self.channels = Channels(self.pool)
        self.messages = Messages(self.pool)
        self.attachments = Attachments(self.pool)
        self.reactions = Reactions(self.pool)
        self.emojis = Emojis(self.pool)
        self.message_emojis = MessageEmojis(self.pool)

        self.logger = Logger(self.pool)
        self.leaderboard = Leaderboard(self.pool)
        self.emojiboard = Emojiboard(self.pool)
        self.subjects = Subjects(self.pool)
        self.seasons = Seasons(self.pool)
