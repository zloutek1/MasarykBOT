# pyright: reportUnnecessaryIsInstance=false
 
import logging
import re
from typing import Optional, Set, TypeVar, cast

import discord
from discord.abc import GuildChannel, Messageable, Snowflake
from discord.ext import commands
from discord.utils import find, get
from emoji import get_emoji_regexp

from bot.constants import CONFIG



log = logging.getLogger(__name__)
BotT = TypeVar('BotT', bound=commands.Bot | commands.AutoShardedBot)



class UnicodeEmoji(commands.Converter[str]):
    async def convert(self, ctx: commands.Context[BotT], argument: str) -> str:
        if not re.match(get_emoji_regexp(), argument):
            raise commands.BadArgument('Emoji "{}" not found'.format(argument))
        return argument



Action = GuildChannel | discord.Role
Emote = discord.Emoji | discord.PartialEmoji | UnicodeEmoji
DISCORD_MAX_CHANNEL_OVERWRITES = 500
E_MISSING_ACCESS = 50001
E_MISSING_PERMISSIONS = 50013



class RolemenuService:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        
    
    @staticmethod
    def is_rolemenu_channel(channel_id: int) -> bool:
        return channel_id in (guild.channels.about_you for guild in CONFIG.guilds)


    async def fetch_message(self, payload: discord.RawReactionActionEvent | discord.RawMessageUpdateEvent) -> discord.Message:
        channel = await self.bot.fetch_channel(payload.channel_id)
        if not isinstance(channel, Messageable):
            raise AssertionError(f"channel {channel} is not messageable")
        return await channel.fetch_message(payload.message_id)


    def get_rolemenu_row(self, message: discord.Message, emoji: discord.PartialEmoji) -> Optional[str]:
        rows = message.content.split('\n')
        return find(lambda row: row.startswith(str(emoji)), rows)


    def parse_action(self, message: discord.Message, emoji: discord.PartialEmoji) -> Optional[Action]:
        assert message.guild
        if not (row := self.get_rolemenu_row(message, emoji)):
            return None
        
        action = row.split(" ", 1)[1]
        
        return (
            self.parse_channel(message.guild, action) or
            self.parse_role(message.guild, action)
        )
        
    
    @staticmethod
    def parse_channel(guild: discord.Guild, text: str) -> Optional[GuildChannel]:
        if (match := re.match(r"<#(\d+)>", text)):
            return get(guild.channels, id=int(match.group(1)))
        return None
    

    @staticmethod
    def parse_role(guild: discord.Guild, text: str) -> Optional[discord.Role]:
        if (match := re.match(r"<@&(\d+)>", text)):
            return get(guild.roles, id=int(match.group(1)))
        return None
        

    @staticmethod
    def list_emojis(message: discord.Message) -> Set[str]:
        rows = message.content.split('\n')
        return set(row.split(' ', 1)[0] for row in rows)


    async def show_channel(self, channel: GuildChannel, user: discord.Member) -> None:
        if role := get(channel.guild.roles, name=f"📁{channel.name}"):
            log.info("adding role %s to %s", str(role), user)
            await user.add_roles(role)

        elif len(channel.overwrites) <= DISCORD_MAX_CHANNEL_OVERWRITES:
            log.info("adding permission overwrite to %s", user)
            await channel.set_permissions(user, overwrite=discord.PermissionOverwrite(read_messages=True))
           
        else:
            await self._migrate_overrides_to_role(channel, user)

    
    async def hide_channel(self, channel: GuildChannel, user: discord.Member) -> None:
        if role := get(channel.guild.roles, name=f"📁{channel.name}"):
            await user.remove_roles(role)
        else:
            await channel.set_permissions(user, overwrite=None)


    async def _migrate_overrides_to_role(self, channel: GuildChannel, user: discord.Member) -> None:
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



class Rolemenu(commands.Cog):
    def __init__(self, bot: commands.Bot, service: RolemenuService = None) -> None:
        self.bot = bot
        self.service = service or RolemenuService(bot)


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        await self.on_raw_reaction_update(payload)


    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        await self.on_raw_reaction_update(payload)


    async def on_raw_reaction_update(self, payload: discord.RawReactionActionEvent) -> None:
        if not self.service.is_rolemenu_channel(payload.channel_id):
            return

        message = await self.service.fetch_message(payload)
        if not (action := self.service.parse_action(message, payload.emoji)):
            return

        assert message.guild
        user = await message.guild.fetch_member(payload.user_id)

        if payload.event_type == "REACTION_ADD":
            await self._reaction_add(message.guild, user, action)
        elif payload.event_type == "REACTION_REMOVE":
            await self._reaction_remove(message.guild, user, action)
        else:
            raise NotImplementedError


    async def _reaction_add(self, guild: discord.Guild, user: discord.Member, action: Action) -> None:
        if isinstance(action, discord.Role):
            await user.add_roles(cast(Snowflake, action))
            log.info("added role %s to %s", action, user)

        elif isinstance(action, discord.TextChannel):
            await self.service.show_channel(action, user)
            log.info("shown channel %s to %s", action, user)

        else:
            raise NotImplementedError


    async def _reaction_remove(self, guild: discord.Guild, user: discord.Member, action: Action) -> None:
        if isinstance(action, discord.Role):
            await user.remove_roles(cast(Snowflake, action))
            log.info("removed role %s from %s", action, user)

        if isinstance(action, discord.TextChannel):
            await self.service.hide_channel(action, user)
            log.info("hidden channel %s from %s", action, user)

        else:
            raise NotImplementedError


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not self.service.is_rolemenu_channel(message.channel.id):
            return

        for row in message.content.split("\n"):
            emoji = row.strip().split(" ", 1)[0]
            await message.add_reaction(emoji)
            

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        if not self.service.is_rolemenu_channel(payload.channel_id):
            return
        
        message = await self.service.fetch_message(payload)
        seen_emojis = self.service.list_emojis(message)
        
        for emoji in seen_emojis:
            await message.add_reaction(emoji)
            
        for reaction in message.reactions:
            if str(reaction.emoji) not in seen_emojis:
                await message.clear_reaction(reaction.emoji)


    # TODO: implement balancing

    

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Rolemenu(bot))
