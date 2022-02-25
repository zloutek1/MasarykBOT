import logging
import re
from typing import Any, List, Optional, Tuple, TypeVar, Union, cast

from bot.cogs.utils.context import Context, GuildChannel
from bot.constants import Config
from disnake import (Emoji, Guild, Member, Message, PartialEmoji,
                     PermissionOverwrite, RawMessageUpdateEvent,
                     RawReactionActionEvent, Reaction, Role, TextChannel, User)
from disnake.abc import Messageable, Snowflake
from disnake.errors import Forbidden, HTTPException
from disnake.ext import commands
from disnake.ext.commands.core import AnyContext
from disnake.utils import find, get
from emoji import UNICODE_EMOJI

log = logging.getLogger(__name__)

class UnicodeEmoji(commands.Converter[str]):
    """
    discord.py's way of handling emojis is [Emoji, PartialEmoji, str]
    UnicodeEmoji accepts str only if it is present
    in UNICODE_EMOJI list
    """
    async def convert(self, _ctx: AnyContext, argument: str) -> str:
        if argument not in UNICODE_EMOJI:
            raise commands.BadArgument('Emoji "{}" not found'.format(argument))
        return argument


Emote = Union[Emoji, PartialEmoji, UnicodeEmoji]
E_MISSING_ACCESS = 50001
E_MISSING_PERMISSIONS = 50013


class Rolemenu(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent) -> None:
        await self.on_raw_reaction_update(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent) -> None:
        await self.on_raw_reaction_update(payload)

    async def on_raw_reaction_update(self, payload: RawReactionActionEvent) -> None:
        """
        Detect a user reacting on a message inside a `about_you` channel
        and either toggle a visiblity of a channel
        or         toggle a role for the user
        """

        about_you_channels = [guild.channels.about_you for guild in Config.guilds]
        if payload.channel_id not in about_you_channels:
            return

        if payload.guild_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        channel = get(guild.text_channels, id=payload.channel_id)
        if channel is None:
            return

        message = await channel.fetch_message(payload.message_id)
        author = guild.get_member(payload.user_id)

        if author is None or author == self.bot.user:
            return

        if not (row := find(lambda row: row.startswith(str(payload.emoji)), message.content.split('\n'))):
            return

        try:
            desc = row.split(" ", 1)[1]
        except ValueError:
            return

        try:
            if payload.event_type == "REACTION_ADD":
                await self._reaction_add(guild, author, desc)
            else:
                await self._reaction_remove(guild, author, desc)
        except Forbidden as err:
            if err.code == E_MISSING_ACCESS:
                log.warning("Missing access for option %s", row)

    async def _reaction_add(self, guild: Guild, user: Member, desc: str) -> None:
        """
        Add role or show channel to a user
        @param desc - name of a role or channel
        """

        if role := self.get_role(guild, desc):
            await user.add_roles(cast(Snowflake, role))
            log.info("added role %s to %s", str(role), user)
            return

        if channel := self.get_text_channel(guild, desc):
            await channel.set_permissions(user,
                                          overwrite=PermissionOverwrite(read_messages=True))
            log.info("shown channel %s to %s", str(channel), user)
            return

    async def _reaction_remove(self, guild: Guild, author: Member, desc: str) -> None:
        """
        Remove role or hide channel from a user
        @param desc - name of a role or channel
        """

        if role := self.get_role(guild, desc):
            await author.remove_roles(cast(Snowflake, role))
            log.info("removed role %s from %s", str(role), author)
            return

        if channel := self.get_text_channel(guild, desc):
            await channel.set_permissions(author, overwrite=None)
            log.info("hidden channel %s from %s", str(channel), author)
            return

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        """
        Detect a user sending a message inside a `about_you` channel
        detects lines in a format
            `:emoji: #channel` or `:emoji: @role`
        and adds corresponding emojis to the message
        """

        if message.guild is None:
            return

        if (guild_config := get(Config.guilds, id=message.guild.id)) is None:
            return
        if message.channel.id != guild_config.channels.about_you:
            return

        for row in message.content.split("\n"):
            emoji = row.strip().split(" ", 1)[0]
            try:
                await message.add_reaction(emoji)
            except Forbidden as err:
                if err.code == E_MISSING_PERMISSIONS:
                    log.warning("missing permissions in %s", message.guild)
            except HTTPException:
                continue

    @staticmethod
    def get_role(guild: Guild, string: str) -> Optional[Role]:
        if not (match := re.match(r"<@&(\d+)>", string)):
            return None
        role_id = int(match.group(1))
        return get(guild.roles, id=role_id)

    @staticmethod
    def get_text_channel(guild: Guild, string: str) -> Optional[TextChannel]:
        if not (match := re.match(r"<#(\d+)>", string)):
            return None
        channel_id = int(match.group(1))
        return get(guild.text_channels, id=channel_id)

    def get_emoji(self, string: str) -> Optional[Emoji]:
        if not (match := re.match(r"<:.*:(\d+)>", string)):
            return None
        emoji_id = match.group(1)
        return get(self.bot.emojis, id=int(emoji_id))

    @staticmethod
    def get_reaction(message: Message, emoji: str) -> Optional[Reaction]:
        for react in message.reactions:
            if str(react.emoji) == emoji:
                return react
        return None

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: RawMessageUpdateEvent) -> None:
        """
        Detect a user editing a message inside a `about_you` channel
        detects lines in a format
            `:emoji: #channel` or `:emoji: @role`
        and adds corresponding emojis to the message
        """

        about_you_channels = [guild.channels.about_you for guild in Config.guilds]
        if payload.channel_id not in about_you_channels:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if channel is None or not isinstance(channel, Messageable):
            return

        message = await channel.fetch_message(payload.message_id)

        assert 'content' in payload.data, "ERROR: key content expected in payload response"

        seen_emojis = set()
        for row in cast(Any, payload.data)['content'].split("\n"):
            emoji = row.strip().split(" ", 1)[0]
            seen_emojis.add(emoji)
            try:
                await message.add_reaction(emoji)
            except HTTPException:
                continue

        for reaction in message.reactions:
            if str(reaction.emoji) not in seen_emojis:
                await message.clear_reaction(reaction.emoji)


    @commands.Cog.listener()
    async def on_ready(self) -> None:
        about_you_channels = [guild.channels.about_you for guild in Config.guilds]
        for channel_id in about_you_channels:
            channel = self.bot.get_channel(channel_id)
            if channel is None or not isinstance(channel, TextChannel):
                continue

            async for message in channel.history():
                if not message.reactions:
                    continue

                await self.parse_and_balance(channel, message)

    async def parse_and_balance(self, channel: TextChannel, message: Message) -> None:
        assert message.guild is not None, "ERROR: can only parse inside a guild"

        for row in message.content.split("\n"):
            emoji, desc = self.parse(row)

            if emoji is None or desc is None:
                continue

            if role := self.get_role(message.guild, desc):
                await self.balance_role(message, emoji, role)

            try:
                await self.balance_channel(message, emoji, channel)
            except Forbidden as err:
                if err.code == E_MISSING_ACCESS:
                    log.warning("Missing access for option %s", row)
            except TimeoutError as err:
                log.warning("Balancing rolemenu for guild %s timed out", message.guild)

    @staticmethod
    def parse(message: str) -> Tuple[Optional[str], Optional[str]]:
        try:
            emoji, desc = message.split(" ", 1)
            return emoji, desc
        except ValueError:
            return None, None
        except IndexError:
            return None, None

    async def balance_role(self, message: Message, emoji: str, role: Role) -> None:
        reaction = self.get_reaction(message, emoji)
        if reaction is None:
            return

        async for user in reaction.users():
            if isinstance(user, User):
                await message.remove_reaction(emoji, cast(Snowflake, user))
                continue

            has_role = get(user.roles, id=role.id)
            if not has_role:
                log.info("added role %s to %s", str(role), user)
                await user.add_roles(cast(Snowflake, role))

        for user in role.members:
            has_reacted = await reaction.users().get(id=user.id)
            if not has_reacted:
                log.info("removed role %s to %s", str(role), user)
                await user.remove_roles(cast(Snowflake, role))

    async def balance_channel(self, message: Message, emoji: str, channel: TextChannel) -> None:
        reaction = self.get_reaction(message, emoji)
        if reaction is None:
            return

        async for user in reaction.users():
            if isinstance(user, User):
                await message.remove_reaction(emoji, cast(Snowflake, user))
                continue

            if not channel.permissions_for(user).read_messages:
                log.info("showing channel %s to %s", str(channel), user)
                await channel.set_permissions(user,
                                              overwrite=PermissionOverwrite(read_messages=True))

        visible_to = {user: overwrite
                      for (user, overwrite) in channel.overwrites.items()
                      if overwrite.read_messages and isinstance(user, Member) and not user.bot}
        for user in visible_to:
            has_reacted = await reaction.users().get(id=user.id)
            if not has_reacted:
                log.info("hide channel %s to %s", str(channel), user)
                await channel.set_permissions(user,
                                              overwrite=None)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Rolemenu(bot))
