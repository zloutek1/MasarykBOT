import io
import discord
from discord.utils import get
from discord.ext import commands


class Context(commands.Context):
    """
    custom Context object passed in every ctx variable
    in your commands. provides some useful getter shortcuts
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = self.bot.db

    def get_category(self, name=None, **kwargs):
        if name is not None:
            kwargs.update({"name": name})
        return get(self.guild.categories, **kwargs)

    def get_channel(self, name=None, **kwargs):
        if name is not None:
            kwargs.update({"name": name})
        return get(self.guild.channels, **kwargs)

    def get_role(self, name=None, **kwargs):
        if name is not None:
            kwargs.update({"name": name})
        return get(self.guild.roles, **kwargs)

    def get_emoji(self, name=None, **kwargs):
        if name is not None:
            kwargs.update({"name": name})
        return get(self.bot.emojis, **kwargs)

    def get_user(self, name=None, **kwargs):
        if name is not None:
            kwargs.update({"name": name})
        return get(self.guild.members, **kwargs)

    def channel_name(self, text):
        return ("-".join(text.lower().split())
                   .replace("+", "﹢")
                   .replace(".", "․")
                   .replace("-", "–"))

    async def safe_delete(self, **kwargs):
        try:
            await self.message.delete(**kwargs)
        except discord.errors.NotFound:
            pass

    async def safe_send(self, content, *, escape_mentions=True, **kwargs):
        if escape_mentions:
            content = discord.utils.escape_mentions(content)

        if len(content) > 2000:
            fp = io.BytesIO(content.encode())
            kwargs.pop('file', None)
            return await self.send(file=discord.File(fp, filename='message_too_long.txt'), **kwargs)
        else:
            return await self.send(content)

    async def send_embed(self, content, name="Message", delete_after=None, **kwargs):
        from datetime import datetime

        embed = discord.Embed(**kwargs)
        embed.add_field(name=name, value=content)
        embed.set_footer(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        await self.send(embed=embed, delete_after=delete_after)

    async def send_success(self, content, delete_after=None):
        await self.send_embed(content,
                              name="Success",
                              delete_after=delete_after,
                              color=discord.Color.green())

    async def send_error(self, content, delete_after=None):
        await self.send_embed(content,
                              name="Error",
                              delete_after=delete_after,
                              color=discord.Color.red())
