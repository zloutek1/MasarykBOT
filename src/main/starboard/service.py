import asyncio
import math
import weakref

import discord
from dependency_injector.wiring import Provide
from discord.ext import commands

from core.context import Context
from core.database import DatabaseError
from core.inject import Inject
from starboard.config.model import StarboardConfig
from starboard.config.repository import StarboardConfigRepository
from starboard.embed import StarboardEmbed

StarableChannel = discord.TextChannel | discord.VoiceChannel | discord.Thread


class StarError(commands.CheckFailure):
    pass


class StarboardService:
    def __init__(
            self,
            bot: commands.Bot,
            config_repository: StarboardConfigRepository = Provide[Inject.repository.starboard_config]
    ):
        self.bot = bot
        self.config_repository = config_repository
        self._message_cache: dict[int, discord.Message] = {}
        self._locks: weakref.WeakValueDictionary[int, asyncio.Lock] = weakref.WeakValueDictionary()

    async def create(self, ctx: Context, channel_name: str) -> str:
        """ Creates a starboard channel in the Discord server. """

        overwrites = await self._channel_permissions(ctx)
        reason = f'{ctx.author.mention} (ID: {ctx.author.id}) has created the starboard channel.'

        print(ctx.guild.channels)
        starboard_channel = discord.utils.find(lambda channel: channel.name == channel_name, ctx.guild.channels)

        if starboard_channel is None:
            try:
                starboard_channel = await ctx.guild.create_text_channel(
                    name=channel_name,
                    overwrites=overwrites,
                    reason=reason
                )
            except discord.Forbidden:
                raise StarError('\N{NO ENTRY SIGN} I do not have permissions to create a channel.')
            except discord.HTTPException:
                raise StarError('\N{NO ENTRY SIGN} This channel name is bad or an unknown error happened.')

        config = StarboardConfig()
        config.guild_id = ctx.guild.id
        config.starboard_channel_id = starboard_channel.id

        try:
            await self.config_repository.create(config)
            return f'Starboard channel {starboard_channel.mention} created successfully'
        except DatabaseError:
            await starboard_channel.delete(reason='Failure to commit to create the ')
            raise StarError('Could not create the channel due to an internal error. Join the bot support server for '
                            'help.')

    @staticmethod
    async def _channel_permissions(ctx) -> dict[discord.Role | discord.Member, discord.PermissionOverwrite]:
        overwrites = {
            ctx.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_messages=True, embed_links=True,
                read_message_history=True
            ),
            ctx.guild.default_role: discord.PermissionOverwrite(
                read_messages=True, send_messages=False, read_message_history=True
            ),
        }
        return overwrites

    async def redirect(
            self,
            ctx: Context,
            targets: list[StarableChannel | discord.Member],
            starboard_channel: discord.TextChannel
    ) -> str:
        """ Configures the redirection of starboard messages to a specific starboard channel. """

        starboard_configs = await self.config_repository.find_redirects(ctx.guild.id, starboard_channel.id)
        if not starboard_configs:
            raise StarError(f'\N{NO ENTRY SIGN} Starboard channel {starboard_channel.mention} not found in database.')

        for config in starboard_configs:
            await self.config_repository.delete(config.id)

        for target in targets:
            config = StarboardConfig()
            config.guild_id = ctx.guild.id
            config.target_id = target.id
            config.starboard_channel_id = starboard_channel.id
            await self.config_repository.create(config)

        mentions = ', '.join(target.mention for target in targets)
        return f'Starboard messages from {mentions} will be redirected to {starboard_channel.mention}'

    async def reaction_added(self, payload: discord.RawReactionActionEvent) -> None:
        lock = self._locks.get(payload.guild_id)
        if lock is None:
            self._locks[payload.guild_id] = lock = asyncio.Lock()

        async with lock:
            await self._reaction_added(payload)

    async def _reaction_added(self, payload: discord.RawReactionActionEvent) -> None:
        guild = self.bot.get_guild(payload.guild_id) or await self.bot.fetch_guild(payload.guild_id)
        if guild is None:
            return None

        channel = guild.get_channel_or_thread(payload.channel_id) or await guild.fetch_channel(payload.channel_id)
        if not isinstance(channel, StarableChannel):
            return None

        user = payload.member or await guild.fetch_member(payload.user_id)
        if user is None or user.bot:
            return None

        message = await self.get_message(channel, payload.message_id)
        if message is None:
            raise StarError('\N{BLACK QUESTION MARK ORNAMENT} This message could not be found.')

        reaction = discord.utils.find(lambda r: payload.emoji == r.emoji, message.reactions)
        if reaction is None:
            return None

        starboard_configs = await self.config_repository.find_starboards(channel.guild.id, channel.id)
        if not starboard_configs:
            raise StarError(f'\N{WARNING SIGN} No starboard configurations found for {channel.mention}')

        for config in starboard_configs:
            await self.star_message(message, reaction, config)

    async def star_message(self, message: discord.Message, reaction: discord.Reaction, config: StarboardConfig):
        if self.should_ignore_message(message, reaction, config):
            return None

        starboard_channel = message.channel.guild.get_channel(config.starboard_channel_id)
        assert isinstance(starboard_channel, discord.TextChannel)

        if not starboard_channel.permissions_for(starboard_channel.guild.me).send_messages:
            raise StarError('\N{NO ENTRY SIGN} Cannot post messages in starboard channel.')

        embed = StarboardEmbed(message)

        await starboard_channel.send(embed=embed)

    def should_ignore_message(
            self,
            message: discord.Message,
            reaction: discord.Reaction,
            config: StarboardConfig
    ) -> bool:
        ignore_channels = []
        channel = message.channel

        return (
            # self._is_recently_starred()
                channel.id in ignore_channels
                or (isinstance(channel, discord.Thread) and channel.parent_id in ignore_channels)
                or channel.type == discord.ChannelType.private_thread
                # or self._should_ignore_emoji(cfg)
                or reaction.count < config.min_limit
                or reaction.count < self._calculate_ignore_score(message, reaction, config)
        )

    @staticmethod
    def _calculate_ignore_score(
            message: discord.Message,
            reaction: discord.Reaction,
            config: StarboardConfig
    ) -> float:
        star_limit: float = config.min_limit or math.inf

        if message.channel.member_count > 100:
            star_limit += 10

        if reaction.emoji in ('⭐', '🌟'):
            star_limit -= 5

        return star_limit

    async def get_message(self, channel: discord.abc.Messageable, message_id: int) -> discord.Message | None:
        try:
            return self._message_cache[message_id]
        except KeyError:
            msg = await channel.fetch_message(message_id)
            self._message_cache[message_id] = msg
            return msg
