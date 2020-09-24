# pylint: disable=abstract-method
# pylint: disable=arguments-differ
# pylint: disable=line-too-long


import asyncio
import asyncpg


class Table:
    def __init__(self, db):
        self.db = db

    async def prepare_one(self, obj):
        raise NotImplementedError("prepare_one form object not implemented for this table")

    async def prepare(self, objs):
        raise NotImplementedError("prepare form objects not implemented for this table")

    async def select(self, data):
        raise NotImplementedError("select not implemented for this table")

    async def insert(self, data):
        raise NotImplementedError("insert not implemented for this table")

    async def update(self, data):
        raise NotImplementedError("update not implemented for this table")

    async def delete(self, data):
        raise NotImplementedError("hard delete not implemented for this table, perhaps try soft delete?")

    async def soft_delete(self, data):
        raise NotImplementedError("soft delete not implemented for this table, perhaps try hard delete?")


class Guilds(Table):
    @staticmethod
    async def prepare_one(guild):
        return (guild.id, guild.name, str(guild.icon_url), guild.created_at)

    async def prepare(self, guilds):
        return [await self.prepare_one(guild) for guild in guilds]

    async def insert(self, data):
        async with self.db.acquire() as conn:
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

    async def soft_delete(self, ids):
        async with self.db.acquire() as conn:
            await conn.executemany("UPDATE server.guilds SET deleted_at=NOW() WHERE id = $1;", ids)


class Categories(Table):
    @staticmethod
    async def prepare_one(category):
        return (category.guild.id, category.id, category.name, category.position, category.created_at)

    async def prepare(self, categories):
        return [await self.prepare_one(category) for category in categories]

    async def insert(self, data):
        async with self.db.acquire() as conn:
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

    async def update(self, data):
        await self.insert(data)

    async def soft_delete(self, ids):
        async with self.db.acquire() as conn:
            await conn.executemany("UPDATE server.categories SET deleted_at=NOW() WHERE id = $1;", ids)


class Roles(Table):
    @staticmethod
    async def prepare_one(role):
        return (role.guild.id, role.id, role.name, hex(role.color.value), role.created_at)

    async def prepare(self, roles):
        return [await self.prepare_one(role) for role in roles]

    async def insert(self, data):
        async with self.db.acquire() as conn:
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

    async def soft_delete(self, ids):
        async with self.db.acquire() as conn:
            await conn.executemany("UPDATE server.roles SET deleted_at=NOW() WHERE id = $1;", ids)


class Members(Table):
    @staticmethod
    async def prepare_one(member):
        return (member.id, member.name, str(member.avatar_url), member.created_at)

    async def prepare(self, members):
        return [await self.prepare_one(member) for member in members]

    async def prepare_from_message(self, message):
        return [await self.prepare_one(message.author)]

    async def insert(self, data):
        async with self.db.acquire() as conn:
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

    async def soft_delete(self, ids):
        async with self.db.acquire() as conn:
            await conn.executemany("UPDATE server.members SET deleted_at=NOW() WHERE id = $1;", ids)


class Channels(Table):
    @staticmethod
    async def prepare_one(channel):
        category_id = channel.category.id if channel.category is not None else None
        return (channel.guild.id, category_id, channel.id, channel.name, channel.position, channel.created_at)

    async def prepare(self, channels):
        return [await self.prepare_one(channel) for channel in channels]

    async def insert(self, data):
        async with self.db.acquire() as conn:
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

    async def update(self, data):
        await self.insert(data)

    async def soft_delete(self, ids):
        async with self.db.acquire() as conn:
            await conn.executemany("UPDATE server.channels SET deleted_at=NOW() WHERE id = $1;", ids)


class Messages(Table):
    @staticmethod
    async def prepare_one(message):
        return (message.channel.id, message.author.id, message.id, message.content, message.created_at, message.edited_at)

    async def prepare(self, message):
        return [await self.prepare_one(message)]

    async def insert(self, messages):
        async with self.db.acquire() as conn:
            await conn.executemany("""
                INSERT INTO server.messages AS m (channel_id, author_id, id, content, created_at, edited_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (id) DO UPDATE
                    SET content=$4,
                        created_at=$5,
                        edited_at=$6
                    WHERE m.content<>excluded.content OR
                          m.created_at<>excluded.created_at OR
                          m.edited_at<>excluded.edited_at
            """, messages)

    async def update(self, messages):
        await self.insert(messages)

    async def soft_delete(self, ids):
        async with self.db.acquire() as conn:
            await conn.executemany("UPDATE server.messages SET deleted_at=NOW() WHERE id = $1;", ids)


class Attachments(Table):
    @staticmethod
    async def prepare_one(message, attachment):
        return (message.id, attachment.id, attachment.filename, attachment.url)

    async def prepare(self, message):
        return [await self.prepare_one(message, attachment) for attachment in message.attachments]

    async def insert(self, attachments):
        async with self.db.acquire() as conn:
            await conn.executemany("""
                INSERT INTO server.attachments AS a (message_id, id, filename, url)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO UPDATE
                    SET filename=$3,
                        url=$4
                    WHERE a.filename<>excluded.filename OR
                          a.url<>excluded.url
            """, attachments)


class Reactions(Table):
    @staticmethod
    async def prepare_one(reaction):
        import emoji
        user_ids = await reaction.users().map(lambda member: member.id).flatten()
        return (reaction.message.id, emoji.demojize(str(reaction.emoji)), user_ids)

    async def prepare(self, message):
        return [await self.prepare_one(reaction) for reaction in message.reactions]

    async def insert(self, reactions):
        async with self.db.acquire() as conn:
            await conn.executemany("""
                INSERT INTO server.reactions AS r (message_id, name, member_ids)
                VALUES ($1, $2, $3)
                ON CONFLICT (message_id, name) DO NOTHING
            """, reactions)


class Emojis(Table):
    REGEX = r"((?::\w+(?:~\d+)?:)|(?:<\d+:\w+:>))"

    @staticmethod
    async def prepare(message):
        import re
        import emoji
        from collections import Counter

        emojis = re.findall(Emojis.REGEX, emoji.demojize(message.content))

        return [(message.id, emote, count) for (emote, count) in Counter(emojis).items()]

    async def insert(self, emojis):
        async with self.db.acquire() as conn:
            await conn.executemany("""
                INSERT INTO server.emojis AS r (message_id, name, count)
                VALUES ($1, $2, $3)
                ON CONFLICT (message_id, name) DO NOTHING
            """, emojis)


class Logger(Table):
    async def select(self, guild_id):
        async with self.db.acquire() as conn:
            return await conn.fetch("SELECT * FROM cogs.logger WHERE guild_id = $1", guild_id)

    async def start_process(self, guild_id, from_date, to_date):
        async with self.db.acquire() as conn:
            await conn.execute("INSERT INTO cogs.logger VALUES ($1, $2, $3, NULL)", guild_id, from_date, to_date)

    async def mark_process_finished(self, guild_id, from_date, to_date, is_first_week):
        async with self.db.acquire() as conn:
            if is_first_week:
                await conn.execute("UPDATE cogs.logger SET finished_at = NOW() WHERE guild_id = $1 AND finished_at IS NULL", guild_id)
            else:
                async with conn.transaction():
                    await conn.execute("DELETE FROM cogs.logger WHERE guild_id = $1 AND from_date = $2 AND to_date = $3", guild_id, from_date, to_date)
                    await conn.execute("UPDATE cogs.logger SET to_date = $3, finished_at = NOW() WHERE guild_id = $1 AND to_date = $2 AND finished_at IS NOT NULL", guild_id, from_date, to_date)


class Leaderboard(Table):
    async def refresh(self):
        async with self.db.acquire() as conn:
            try:
                await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY cogs.leaderboard")
            except Exception:
                await conn.execute("REFRESH MATERIALIZED VIEW cogs.leaderboard")

    async def preselect(self, guild_id, ignored_users, channel_id):
        async with self.db.acquire() as conn:
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

    async def get_top10(self):
        async with self.db.acquire() as conn:
            return await conn.fetch("SELECT * FROM ldb_lookup LIMIT 10")

    async def get_around(self, author_id):
        async with self.db.acquire() as conn:
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
                    WHERE sent_total = (SELECT * FROM desired_count)
                ) UNION (
                    SELECT *
                    FROM ldb_lookup
                    WHERE sent_total < (SELECT * FROM desired_count) AND author_id <> $1 LIMIT 2
                ) ORDER BY sent_total DESC
            """, author_id)


class Emojiboard(Table):
    async def refresh(self):
        async with self.db.acquire() as conn:
            await conn.execute("REFRESH MATERIALIZED VIEW cogs.emojiboard")

    async def select(self, guild_id, ignored_users, channel_id, author_id, emoji):
        async with self.db.acquire() as conn:
            return await conn.fetch("""
                SELECT
                    emoji.name,
                    COUNT(*) AS sent_total
                FROM cogs.emojiboard AS emoji
                INNER JOIN server.channels AS channel
                    ON channel_id = channel.id
                WHERE guild_id = $1::bigint AND
                      author_id<>ALL($2::bigint[]) AND
                      ($3::bigint IS NULL OR channel_id = $3) AND
                      ($4::bigint IS NULL OR author_id = $4) AND
                      ($5::text IS NULL OR emoji.name = $5)
                GROUP BY emoji.name
                ORDER BY sent_total DESC
                LIMIT 10
            """, guild_id, ignored_users, channel_id, author_id, emoji)


class Subjects(Table):
    async def find(self, code, faculty="FI"):
        async with self.db.acquire() as conn:
            return await conn.fetch("SELECT * FROM muni.subjects WHERE LOWER(code) LIKE LOWER($1) AND faculty = $2", code, faculty)

    async def find_registered(self, guild_id, code):
        async with self.db.acquire() as conn:
            return await conn.fetchrow("""
                SELECT * FROM muni.registers
                WHERE guild_id = $1 AND LOWER(code) LIKE LOWER($2)""", guild_id, code)

    async def sign_user(self, guild_id, code, member_id):
        async with self.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO muni.registers AS r (guild_id, code, member_ids)
                       VALUES ($1, $2, ARRAY[$3::bigint])
                ON CONFLICT (guild_id, code) DO UPDATE
                    SET member_ids = array_append(r.member_ids, $3::bigint)
                    WHERE $3::bigint <> ALL(r.member_ids);
            """, guild_id, code, member_id)

    async def unsign_user(self, guild_id, code, member_id):
        async with self.db.acquire() as conn:
            await conn.execute("""
                UPDATE muni.registers
                    SET member_ids = array_remove(member_ids, $3::bigint)
                    WHERE guild_id = $1 AND
                          LOWER(code) = LOWER($2) AND
                          $3 = ANY(member_ids);
            """, guild_id, code, member_id)

    async def get_category(self, guild_id, code):
        async with self.db.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM muni.subject_category WHERE LOWER(code) LIKE LOWER($1) AND guild_id = $2",
                code, guild_id)

    async def set_channel(self, guild_id, code, channel_id):
        async with self.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO muni.subject_server AS ss (guild_id, code, channel_id)
                       VALUES ($1, $2, $3)
                ON CONFLICT (guild_id, code) DO UPDATE
                    SET channel_id = excluded.channel_id
                    WHERE ss.channel_id IS NULL OR ss.channel_id <> excluded.channel_id;
            """, guild_id, code, channel_id)

    async def set_category(self, guild_id, code, category_id):
        async with self.db.acquire() as conn:
            await conn.execute("""
                UPDATE muni.subject_server
                    SET category_id = $3
                    WHERE guild_id = $1 AND LOWER(code) LIKE LOWER($2);
            """, guild_id, code, category_id)

    async def remove_channel(self, guild_id, code):
        async with self.db.acquire() as conn:
            await conn.execute("""
                UPDATE muni.subject_server
                    SET channel_id = NULL
                    WHERE guild_id = $1 AND
                          LOWER(code) = LOWER($2)
            """, guild_id, code)


class Tags(Table):
    async def select(self, guild_id, user_id):
        async with self.db.acquire() as conn:
            return await conn.fetch("SELECT * FROM cogs.tags WHERE guild_id = $1 AND author_id = $2", guild_id, user_id)

    async def get_tag(self, guild_id, name):
        async with self.db.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM cogs.tags WHERE guild_id = $1 AND LOWER(name) = $2", guild_id, name)

    async def find_tags(self, guild_id, name):
        async with self.db.acquire() as conn:
            return await conn.fetch("""
                SELECT name, id FROM cogs.tags
                WHERE guild_id=$1 AND name % $2
                ORDER BY similarity(name, $2) DESC
                LIMIT 100;
            """, guild_id, name)

    async def create_tag(self, guild_id, author_id, name, content):
        async with self.db.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO cogs.tags (guild_id, author_id, name, content)
                    VALUES ($1, $2, $3, $4)
                """, guild_id, author_id, name, content)
                return True
            except asyncpg.UniqueViolationError:
                return False

    async def delete_tag(self, guild_id, author_id, name):
        async with self.db.acquire() as conn:
            await conn.execute("DELETE FROM cogs.tags WHERE guild_id=$1 AND author_id=$2 AND LOWER(name)=$3", guild_id, author_id, name)

    async def edit_tag(self, guild_id, author_id, name, new_content):
        async with self.db.acquire() as conn:
            return await conn.execute("""
                UPDATE cogs.tags
                SET content=$4
                WHERE guild_id=$1 AND author_id=$2 AND LOWER(name)=$3
            """, guild_id, author_id, name, new_content)


class Rolemenu(Table):
    @staticmethod
    async def prepare(message, role, emoji):
        return [(message.channel.id, message.id, role.id, str(emoji))]

    async def insert(self, data):
        async with self.db.acquire() as conn:
            await conn.executemany("""
                INSERT INTO cogs.rolemenu (channel_id, message_id, role_id, emoji)
                VALUES ($1, $2, $3, $4)
            """, data)

    async def select(self, message_id):
        async with self.db.acquire() as conn:
            return await conn.fetchrow("""
                SELECT * FROM cogs.rolemenu
                WHERE message_id = $1
            """, message_id)

class DBBase:
    def __init__(self, pool):
        self.pool = pool

    @classmethod
    def connect(cls, url):
        loop = asyncio.get_event_loop()
        pool = loop.run_until_complete(asyncpg.create_pool(url, command_timeout=60))
        return Database(pool)


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

        self.logger = Logger(self.pool)
        self.leaderboard = Leaderboard(self.pool)
        self.emojiboard = Emojiboard(self.pool)
        self.subjects = Subjects(self.pool)
        self.tags = Tags(self.pool)
        self.rolemenu = Rolemenu(self.pool)
