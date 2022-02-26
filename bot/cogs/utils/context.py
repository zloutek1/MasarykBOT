import asyncio
import io
from contextlib import suppress
from typing import Any, Optional, Union, cast

import disnake as discord
from disnake.errors import HTTPException, NotFound
from disnake.ext import commands
from disnake.utils import get

GuildChannel = Union[
    discord.channel.VoiceChannel,
    discord.channel.StageChannel,
    discord.channel.TextChannel,
    discord.channel.CategoryChannel,
    discord.channel.StoreChannel
]

class Context(commands.Context):
    """
    custom Context object passed in every ctx variable
    in your commands. provides some useful getter shortcuts
    """

    def get_category(self, name: Optional[str] = None, **kwargs: Any) -> Optional[discord.CategoryChannel]:
        assert self.guild, "this method can only be run for guild events"
        if name is not None:
            kwargs.update({"name": name})
        return get(self.guild.categories, **kwargs)

    def get_channel(self, name: Optional[str] = None, **kwargs: Any) -> Optional[GuildChannel]:
        assert self.guild, "this method can only be run for guild events"
        if name is not None:
            kwargs.update({"name": name})
        return get(self.guild.channels, **kwargs)

    def get_role(self, name: Optional[str] = None, **kwargs: Any) -> Optional[discord.Role]:
        assert self.guild, "this method can only be run for guild events"
        if name is not None:
            kwargs.update({"name": name})
        return get(self.guild.roles, **kwargs)

    def get_emoji(self, name: Optional[str] = None, **kwargs: Any) -> Optional[discord.Emoji]:
        if name is not None:
            kwargs.update({"name": name})
        return get(self.bot.emojis, **kwargs)

    def get_member(self, name: Optional[str] = None, **kwargs: Any) -> Optional[discord.Member]:
        assert self.guild, "this method can only be run for guild events"
        if name is not None:
            kwargs.update({"name": name})
        return get(self.guild.members, **kwargs)

    def channel_name(self, text: str) -> str:
        words = (text.lower()
                     .replace("-", "–")
                     .split())

        return ("-".join(words)
                   .replace("+", "﹢")
                   .replace(".", "․")
                   .replace(",", "")
                   .replace("#", "＃")
                   .replace("/", "／")
                   .replace("(", "")
                   .replace(")", "")
                   .replace(":", "꞉"))

    async def safe_delete(self, **kwargs: Any) -> None:
        with suppress(NotFound):
            await self.message.delete(**kwargs)

    async def safe_send(
        self,
        content: str,
        *,
        escape_mentions: bool = True,
        **kwargs: Any
    ) -> discord.Message:

        if escape_mentions:
            content = discord.utils.escape_mentions(content)

        if len(content) > 2000:
            fp = io.BytesIO(content.encode())
            kwargs.pop('file', None)
            return await self.send(file=discord.File(fp, filename='message_too_long.txt'), **kwargs)
        else:
            return await self.send(content)

    async def send_embed(
        self,
        content: str,
        name: str = "Message",
        delete_after: Optional[float] = None,
        **kwargs: Any
    ) -> discord.Message:

        from datetime import datetime, timedelta, timezone
        CEST = timezone(offset=timedelta(hours=+2))
        now = datetime.now(CEST).strftime("%d.%m.%Y %H:%M:%S")

        embed = discord.Embed(**kwargs)
        embed.add_field(name=name, value=content)
        embed.set_footer(text=now)

        return await self.send(embed=embed, delete_after=delete_after)

    async def send_success(
        self,
        content: str,
        delete_after: Optional[float] = None
    ) -> discord.Message:

        return await self.send_embed(
            content,
            name="Success",
            delete_after=delete_after,
            color=discord.Color.green()
        )

    async def send_error(
        self,
        content: str,
        delete_after: Optional[float] = None
    ) -> discord.Message:

        return await self.send_embed(
            content,
            name="Error",
            delete_after=delete_after,
            color=discord.Color.red()
        )

    async def send(self, *args: Any, **kwargs: Any) -> discord.Message:
        message = await super().send(*args, **kwargs)

        with suppress(NotFound):
            await message.add_reaction('\N{WASTEBASKET}')
            asyncio.get_event_loop().create_task(self._wait_for_reaction_or_clear(message))

        return message

    async def reply(self, *args: Any, mention_author: bool = False, **kwargs: Any) -> discord.Message:
        try:
            return await super().reply(*args, mention_author=mention_author, **kwargs)
        except HTTPException:
            return await self.send(*args, **kwargs)

    async def _wait_for_reaction_or_clear(self, message: discord.Message) -> None:
        def react_check(
            reaction: discord.Reaction,
            user: Union[discord.User, discord.Member]
        ) -> bool:

            if user is None or user.id != self.author.id:
                return False

            if reaction.message.id != message.id:
                return False

            return reaction.emoji == '\N{WASTEBASKET}'

        with suppress(NotFound):
            try:
                await self.bot.wait_for('reaction_add', check=react_check, timeout=120.0)
                await message.delete(delay=5)
            except asyncio.TimeoutError:
                await message.clear_reaction('\N{WASTEBASKET}')
