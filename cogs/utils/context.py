import io
import discord
from discord.utils import get
from discord.ext import commands

import re


class _ContextDBAcquire:
    __slots__ = ('ctx', 'timeout')

    def __init__(self, ctx, timeout):
        self.ctx = ctx
        self.timeout = timeout

    def __await__(self):
        return self.ctx._acquire(self.timeout).__await__()

    async def __aenter__(self):
        await self.ctx._acquire(self.timeout)
        return self.ctx.db

    async def __aexit__(self, *args):
        await self.ctx.release()


class Context(commands.Context):
    """
    custom Context object passed in every ctx variable
    in your commands. provides some useful getter shortcuts
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pool = self.bot.pool
        self._db = None

    @property
    def db(self):
        return self._db if self._db else self.pool

    async def _acquire(self, timeout):
        if self._db is None:
            self._db = await self.pool.acquire(timeout=timeout)
        return self._db

    def acquire(self, *, timeout=None):
        """Acquires a database connection from the pool. e.g. ::
            async with ctx.acquire():
                await ctx.db.execute(...)
        or: ::
            await ctx.acquire()
            try:
                await ctx.db.execute(...)
            finally:
                await ctx.release()
        """
        return _ContextDBAcquire(self, timeout)

    async def release(self):
        """Releases the database connection from the pool.
        Useful if needed for "long" interactive commands where
        we want to release the connection and re-acquire later.
        Otherwise, this is called automatically by the bot.
        """
        # from source digging asyncpg source, releasing an already
        # released connection does nothing

        if self._db is not None:
            await self.bot.pool.release(self._db)
            self._db = None

    def get_category(self, name=None, **kwargs):
        kwargs.update({"name": name}) if name is not None else None
        return get(self.guild.categories, **kwargs)

    def get_channel(self, name=None, **kwargs):
        kwargs.update({"name": name}) if name is not None else None
        return get(self.guild.channels, **kwargs)

    def get_role(self, name=None, **kwargs):
        kwargs.update({"name": name}) if name is not None else None
        return get(self.guild.roles, **kwargs)

    def get_emoji(self, name=None, **kwargs):
        kwargs.update({"name": name}) if name is not None else None
        return get(self.bot.emojis, **kwargs)

    def get_user(self, name=None, **kwargs):
        kwargs.update({"name": name}) if name is not None else None
        return get(self.guild.members, **kwargs)

    def channel_name(self, text):
        return re.sub("[^a-zA-Z0-9-]", "", "-".join(text.lower().split()))

    async def safe_send(self, content, *, escape_mentions=True, **kwargs):
        if escape_mentions:
            content = discord.utils.escape_mentions(content)

        if len(content) > 2000:
            fp = io.BytesIO(content.encode())
            kwargs.pop('file', None)
            return await self.send(file=discord.File(fp, filename='message_too_long.txt'), **kwargs)
        else:
            return await self.send(content)

    async def send_embed(self, content, name="Message", **kwargs):
        embed = discord.Embed(**kwargs)
        embed.add_field(name=name, value=content)
        await self.send(embed=embed)
