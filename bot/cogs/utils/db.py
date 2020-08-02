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

    async def prepare(message):
        return await self.prepare_one(message)

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


class Attachments(Table):
    @staticmethod
    async def prepare_one(message, attachment):
        return (message.id, attachment.id, attachment.filename, attachment.url)

    async def prepare(message):
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
        user_ids = await reaction.users().map(lambda member: member.id).flatten()
        return (reaction.message.id, emoji.demojize(str(reaction.emoji)), user_ids)

    async def prepare(message):
        return [await prepare_reaction(reaction) for reaction in message.reactions]

    async def insert(self, reactions):
        async with self.db.acquire() as conn:
            await conn.executemany("""
                INSERT INTO server.reactions AS r (message_id, name, member_ids)
                VALUES ($1, $2, $3)
                ON CONFLICT (message_id, name) DO NOTHING
            """, reactions)


class Emojis(Table):
    async def prepare(message):
        import re
        import emoji

        REGEX = r"((?::\w+(?:~\d+)?:)|(?:<\d+:\w+:>))"
        emojis = re.findall(REGEX, emoji.demojize(message.content))

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
            try:
                await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY cogs.emojiboard")
            except Exception:
                await conn.execute("REFRESH MATERIALIZED VIEW cogs.emojiboard")

    async def select(self, guild_id, ignored_users, channel_id):
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
                      ($3::bigint IS NULL OR channel_id = $3)
                GROUP BY emoji.name
                ORDER BY sent_total DESC
                LIMIT 10
            """, guild_id, ignored_users, channel_id)


class DBAcquire:
    def __init__(self, db, timeout):
        self.db = db
        self.timeout = timeout

    def __await__(self):
        return self.db._acquire(self.timeout).__await__()

    async def __aenter__(self):
        await self.db._acquire(self.timeout)
        return self.db._conn

    async def __aexit__(self, *args):
        await self.db.release()


class DBBase:
    def __init__(self, pool):
        self.pool = pool
        self._conn = None

    @property
    def conn(self):
        return self._conn if self._conn else self.pool

    @classmethod
    def connect(cls, url):
        loop = asyncio.get_event_loop()
        pool = loop.run_until_complete(asyncpg.create_pool(url, command_timeout=60))
        return Database(pool)

    async def _acquire(self, timeout):
        if self._conn is None:
            self._conn = await self.pool.acquire(timeout=timeout)
        return self._conn

    def acquire(self, *, timeout=None):
        """Acquires a database connection from the pool. e.g. ::
            async with self.acquire():
                await self.conn.execute(...)
        or: ::
            await self.acquire()
            try:
                await self.conn.execute(...)
            finally:
                await self.release()
        """
        return DBAcquire(self, timeout)

    async def release(self):
        """Releases the database connection from the pool.
        Useful if needed for "long" interactive commands where
        we want to release the connection and re-acquire later.
        Otherwise, this is called automatically by the bot.
        """
        if self._conn is not None:
            await self.pool.release(self._conn)
            self._conn = None


class Database(DBBase):
    def __init__(self, *args):
        super().__init__(*args)

        self.guilds = Guilds(self)
        self.categories = Categories(self)
        self.roles = Roles(self)
        self.members = Members(self)
        self.channels = Channels(self)
        self.messages = Messages(self)
        self.attachments = Attachments(self)
        self.reactions = Reactions(self)
        self.emojis = Emojis(self)

        self.logger = Logger(self)
        self.leaderboard = Leaderboard(self)
        self.emojiboard = Emojiboard(self)
