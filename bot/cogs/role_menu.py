# pyright: reportUnnecessaryIsInstance=false

import logging
import re
from typing import Optional, Set, TypeVar, cast, Dict

import discord
from discord.abc import GuildChannel, Messageable, Snowflake
from discord.ext import commands
from discord.utils import find, get
from emoji import is_emoji

from bot.cogs.utils.extra_types import GuildMessage
from bot.constants import CONFIG

log = logging.getLogger(__name__)
BotT = TypeVar('BotT', bound=commands.Bot | commands.AutoShardedBot)


class UnicodeEmoji(commands.Converter[str]):
    async def convert(self, ctx: commands.Context[BotT], argument: str) -> str:
        if not is_emoji(argument):
            raise commands.BadArgument('"{}" is not an emoji'.format(argument))
        return argument


Action = GuildChannel | discord.Role
Emote = discord.Emoji | discord.PartialEmoji | UnicodeEmoji
DISCORD_MAX_CHANNEL_OVERWRITES = 500
E_MISSING_ACCESS = 50001
E_MISSING_PERMISSIONS = 50013


class ActionParsingService:
    def parse_action(self, message: GuildMessage, emoji: discord.PartialEmoji) -> Optional[Action]:
        assert (row := self.get_role_menu_row(message, emoji))

        action = row.split(" ", 1)[1]

        return (
                self._parse_channel(message.guild, action) or
                self._parse_role(message.guild, action)
        )

    @staticmethod
    def get_role_menu_row(message: discord.Message, emoji: discord.PartialEmoji) -> Optional[str]:
        rows = message.content.split('\n')
        return find(lambda row: row.startswith(str(emoji)), rows)

    @staticmethod
    def _parse_channel(guild: discord.Guild, text: str) -> Optional[GuildChannel]:
        if match := re.match(r"<#(\d+)>", text):
            return get(guild.channels, id=int(match.group(1)))
        return None

    @staticmethod
    def _parse_role(guild: discord.Guild, text: str) -> Optional[discord.Role]:
        if match := re.match(r"<@&(\d+)>", text):
            return get(guild.roles, id=int(match.group(1)))
        return None


class ChannelActionService:
    async def show_channel(self, channel: GuildChannel, user: discord.Member) -> None:
        if role := get(channel.guild.roles, name=f"📁{channel.name}"):
            log.info("adding role %s to %s", str(role), user)
            await user.add_roles(role)

        elif len(channel.overwrites) <= DISCORD_MAX_CHANNEL_OVERWRITES:
            log.info("adding permission overwrite to %s", user)
            await channel.set_permissions(user, overwrite=discord.PermissionOverwrite(read_messages=True))

        else:
            await self._migrate_overrides_to_role(channel, user)

    @staticmethod
    async def hide_channel(channel: GuildChannel, user: discord.Member) -> None:
        if role := get(channel.guild.roles, name=f"📁{channel.name}"):
            await user.remove_roles(role)
        else:
            await channel.set_permissions(user, overwrite=None)

    @staticmethod
    async def _migrate_overrides_to_role(channel: GuildChannel, user: discord.Member) -> None:
        if not (role := get(channel.guild.roles, name=f"📁{channel.name}")):
            log.info("creating role instead of permission overwrite")
            role = await channel.guild.create_role(name=f"📁{channel.name}")

        for i, (key, overwrite) in enumerate(channel.overwrites.items()):
            if not isinstance(key, discord.Member) or overwrite != discord.PermissionOverwrite(read_messages=True):
                continue

            await key.add_roles(role)
            await channel.set_permissions(key, overwrite=None)

            if i == 10 or len(channel.overwrites) <= max(0, DISCORD_MAX_CHANNEL_OVERWRITES - 10):
                log.info('showing role')
                await channel.set_permissions(role, overwrite=discord.PermissionOverwrite(read_messages=True))
                await user.add_roles(role)

        log.info('adding role overwrite')
        await channel.set_permissions(role, overwrite=discord.PermissionOverwrite(read_messages=True))
        await user.add_roles(role)


class RoleMenuService:
    def __init__(
            self,
            bot: commands.Bot,
            parsing_service: ActionParsingService = None,
            channel_action_service: ChannelActionService = None
    ) -> None:
        self.bot = bot
        self.parsing = parsing_service or ActionParsingService()
        self.channel_action = channel_action_service or ChannelActionService()

    async def load_role_menu_messages(self) -> Dict[int, GuildMessage]:
        result = {}
        for guild_config in CONFIG.guilds:
            channel_id = guild_config.channels.about_you
            if not (channel := self.bot.get_channel(channel_id)):
                continue
            for message in await self._find_role_menu_messages_in_channel(channel):
                result[message.id] = message
        return result

    @staticmethod
    async def _find_role_menu_messages_in_channel(channel: Messageable) -> list[GuildMessage]:
        return [cast(GuildMessage, message) async for message in channel.history() if message.reactions]

    async def execute_add_action(self, user: discord.Member, action: Action) -> None:
        if isinstance(action, discord.Role):
            await user.add_roles(cast(Snowflake, action))
            log.info("added role %s to %s", action, user)
        elif isinstance(action, discord.TextChannel):
            await self.channel_action.show_channel(action, user)
            log.info("shown channel %s to %s", action, user)
        else:
            raise NotImplementedError

    async def execute_remove_action(self, user: discord.Member, action: Action) -> None:
        if isinstance(action, discord.Role):
            await user.remove_roles(cast(Snowflake, action))
            log.info("removed role %s from %s", action, user)
        elif isinstance(action, discord.TextChannel):
            await self.channel_action.hide_channel(action, user)
            log.info("hidden channel %s from %s", action, user)
        else:
            raise NotImplementedError

    async def update_role_menu(self, message):
        seen_emojis = self._list_emojis(message)
        for emoji in seen_emojis:
            await message.add_reaction(emoji)
        for reaction in message.reactions:
            if str(reaction.emoji) not in seen_emojis:
                await message.clear_reaction(reaction.emoji)

    @staticmethod
    def _list_emojis(message: discord.Message) -> Set[str]:
        rows = message.content.split('\n')
        return set(row.split(' ', 1)[0] for row in rows)


class RoleMenu(commands.Cog):
    def __init__(self, bot: commands.Bot, service: RoleMenuService = None) -> None:
        self.bot = bot
        self.service = service or RoleMenuService(bot)
        self.role_menu_messages: Dict[int, GuildMessage] = {}

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.role_menu_messages = await self.service.load_role_menu_messages()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.message_id in self.role_menu_messages:
            await self.on_raw_reaction_update(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.message_id in self.role_menu_messages:
            await self.on_raw_reaction_update(payload)

    async def on_raw_reaction_update(self, payload: discord.RawReactionActionEvent) -> None:
        message = self.role_menu_messages[payload.message_id]
        user = await message.guild.fetch_member(payload.user_id)
        if not (action := self.service.parsing.parse_action(message, payload.emoji)):
            return

        if payload.event_type == "REACTION_ADD":
            await self.service.execute_add_action(user, action)
        elif payload.event_type == "REACTION_REMOVE":
            await self.service.execute_remove_action(user, action)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.channel.id not in (guild.channels.about_you for guild in CONFIG.guilds):
            return

        self.role_menu_messages[message.id] = cast(GuildMessage, message)
        for row in message.content.split("\n"):
            emoji = row.strip().split(" ", 1)[0]
            await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        if payload.message_id not in self.role_menu_messages:
            return

        message = self.role_menu_messages[payload.message_id]
        await self.service.update_role_menu(message)

    # TODO: implement balancing


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RoleMenu(bot))
