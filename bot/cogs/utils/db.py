import asyncio
import asyncpg

from . import schemas


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
            await conn.executemany(schemas.SQL_INSERT_GUILD, data)

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
            await conn.executemany(schemas.SQL_INSERT_CATEGORY, data)

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
            await conn.executemany(schemas.SQL_INSERT_ROLE, data)

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
            await conn.executemany(schemas.SQL_INSERT_USER, data)

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
            await conn.executemany(schemas.SQL_INSERT_CHANNEL, data)

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
            await conn.executemany(schemas.SQL_INSERT_MESSAGE, messages)


class Attachments(Table):
    @staticmethod
    async def prepare_one(message, attachment):
        return (message.id, attachment.id, attachment.filename, attachment.url)

    async def prepare(message):
        return [await self.prepare_one(message, attachment) for attachment in message.attachments]

    async def insert(self, attachments):
        async with self.db.acquire() as conn:
            await conn.executemany(schemas.SQL_INSERT_ATTACHEMNT, attachments)


class Reactions(Table):
    @staticmethod
    async def prepare_one(reaction):
        user_ids = await reaction.users().map(lambda member: member.id).flatten()
        return (reaction.message.id, emoji.demojize(str(reaction.emoji)), user_ids)

    async def prepare(message):
        return [await prepare_reaction(reaction) for reaction in message.reactions]

    async def insert(self, reactions):
        async with self.db.acquire() as conn:
            await conn.executemany(schemas.SQL_INSERT_REACTIONS, reactions)


class Emojis(Table):
    async def prepare(message):
        import re
        import emoji

        REGEX = r"((?::\w+(?:~\d+)?:)|(?:<\d+:\w+:>))"
        emojis = re.findall(REGEX, emoji.demojize(message.content))

        return [(message.id, emote, count) for (emote, count) in Counter(emojis).items()]

    async def insert(self, emojis):
        async with self.db.acquire() as conn:
            await conn.executemany(schemas.SQL_INSERT_EMOJIS, emojis)


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
