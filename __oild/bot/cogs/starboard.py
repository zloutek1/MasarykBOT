from __future__ import annotations
import logging
import math
import re
from datetime import timedelta, timezone
from collections import deque
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, cast
from dataclasses import dataclass

import discord
from discord.ext import commands
from discord.utils import find, get

from src.bot import CONFIG, GuildConfig, StarboardConfig
from src.bot import get_emoji_name

if TYPE_CHECKING:
    from src.bot import MasarykBOT

log = logging.getLogger(__name__)
Id = int


@dataclass
class StarboardContext:
    bot: MasarykBOT
    reaction: discord.Reaction
    message: discord.Message
    channel: discord.TextChannel | discord.Thread
    guild: discord.Guild

    def __str__(self) -> str:
        return '(' + ', '.join([
            f"reaction=<emoji={self.reaction.emoji} count={self.reaction.count}>",
            f"message=<id={self.message.id}>",
            f"channel=<id={self.channel.id} name={self.channel.name}>",
            f"guild=<id={self.guild.id} name={self.guild.name}>"
        ]) + ')'


class StarboardService:
    def __init__(self, bot: MasarykBOT) -> None:
        self.bot = bot

    async def fetch_message(self, payload: discord.RawReactionActionEvent) -> discord.Message:
        channel = await self.bot.fetch_channel(payload.channel_id)
        if not isinstance(channel, discord.abc.Messageable):
            raise AssertionError(f"channel {channel} is not messageable")
        return await channel.fetch_message(payload.message_id)

    def construct_context(self, reaction: discord.Reaction) -> Optional[StarboardContext]:
        if not isinstance(reaction.message.channel, (discord.TextChannel, discord.Thread)):
            return None

        if not reaction.message.guild:
            return None

        return StarboardContext(
            bot=self.bot,
            reaction=reaction,
            message=reaction.message,
            channel=reaction.message.channel,
            guild=reaction.message.guild
        )

    @staticmethod
    async def process_starboard(ctx: StarboardContext) -> Optional[discord.TextChannel | discord.Thread]:
        processor = StarboardProcessingService(ctx)
        return await processor()

    async def get_reply_thread(self, message: discord.Message, depth: int = 16) -> List[str]:
        reply_emoji = get(self.bot.emojis, name="reply")

        if not message.reference or not message.reference.message_id:
            return [message.content]
        if depth <= 0:
            return [f"{reply_emoji} [truncated]"]

        reply = await message.channel.fetch_message(message.reference.message_id)
        replies = await self.get_reply_thread(reply, depth - 1)

        replies.append(f"{reply_emoji} {message.content}" if replies else message.content)
        return replies


class StarboardProcessingService:
    def __init__(self, ctx: StarboardContext) -> None:
        self.ctx = ctx
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.message = ctx.message
        self.reaction = ctx.reaction

    async def __call__(self) -> Optional[discord.TextChannel | discord.Thread]:
        if self.should_ignore_message():
            return None

        StarboardCog.starred_messages.setdefault(self.guild.id, deque(maxlen=50))
        if self.message.id in StarboardCog.starred_messages[self.guild.id]:
            return None

        StarboardCog.starred_messages[self.guild.id].append(self.message.id)

        if await self.is_already_in_starboard():
            StarboardCog.starred_messages[self.guild.id].remove(self.message.id)
            return None

        log.info("adding message with %s reactions to starboard (%s)", self.reaction.count, self.ctx)
        await self.message.add_reaction(self.reaction.emoji)

        (channel_id, channel_name) = self.pick_starboard_channel()

        starboard_channel = (await self.guild.fetch_channel(channel_id)
                             if channel_id else
                             await self.guild.create_text_channel(channel_name))

        assert isinstance(starboard_channel, (discord.TextChannel, discord.Thread))
        return starboard_channel

    def should_ignore_message(self) -> bool:
        assert (cfg := get(CONFIG.guilds, id=self.guild.id))
        assert (star_cfg := cfg.channels.starboard)

        ignore_channels = self._get_channels_to_ignore(cfg)

        return (
            self._is_recently_starred()
            or self.channel.id in ignore_channels
            or (isinstance(self.channel, discord.Thread) and self.channel.parent_id in ignore_channels)
            or self.channel.type == discord.ChannelType.private_thread
            or self._should_ignore_emoji(cfg)
            or self.reaction.count < star_cfg.REACT_LIMIT
            or self.reaction.count < self._calculate_ignore_score()
        )

    def _get_channels_to_ignore(self, cfg: GuildConfig) -> List[int | None]:
        ignore_channels: List[int | None] = [
            cfg.channels.about_you,
            cfg.channels.verification,
            cfg.channels.course.registration_channel if cfg.channels.course else None,
        ]

        if cfg.channels.starboard:
            for pattern in cfg.channels.starboard.channels.ignored:
                if isinstance(pattern, int):
                    ignore_channels.append(pattern)
                else:
                    ignore_channels.extend(
                        channel.id
                        for channel in self.guild.text_channels
                        if re.match(pattern, channel.name)
                    )

        return ignore_channels

    def _should_ignore_emoji(self, cfg: GuildConfig) -> bool:
        if not cfg.channels.starboard:
            return False

        for pattern in cfg.channels.starboard.emojis.ignored:
            if isinstance(self.reaction.emoji, (discord.Emoji, discord.PartialEmoji)):
                if isinstance(pattern, int) and self.reaction.emoji.id == pattern:
                    return True
                elif isinstance(pattern, str) and re.match(str(self.reaction.emoji), pattern):
                    return True
            else:
                if self.reaction.emoji == pattern:
                    return True
        return False

    def _is_recently_starred(self) -> bool:
        return (self.guild.id in StarboardCog.starred_messages and
                self.message.id in StarboardCog.starred_messages[self.guild.id])

    def _calculate_ignore_score(self) -> float:
        assert (cfg := get(CONFIG.guilds, id=self.guild.id))
        assert (star_cfg := cfg.channels.starboard)

        fame_limit: float = star_cfg.REACT_LIMIT or math.inf

        if len(self.channel.members) > 100:
            fame_limit += 10

        fame_limit = self._penalise_channel(star_cfg, fame_limit, by=15)
        fame_limit = self._penalise_spoiler(fame_limit, by=5)
        fame_limit = self._penalise_emoji(star_cfg, fame_limit, by=15)

        if get_emoji_name(self.reaction.emoji) in ('⭐', '🌟'):
            return fame_limit - 5

        return fame_limit

    def _penalise_emoji(self, star_cfg: StarboardConfig, fame_limit: float, *, by: int) -> float:
        for pattern in star_cfg.channels.penalised:
            if isinstance(self.reaction.emoji, (discord.Emoji, discord.PartialEmoji)):
                if isinstance(pattern, int) and self.reaction.emoji.id == pattern:
                    return fame_limit + by
                elif isinstance(pattern, str) and re.match(str(self.reaction.emoji), pattern):
                    return fame_limit + by
            else:
                if self.reaction.emoji == pattern:
                    return fame_limit + by
        return fame_limit

    def _penalise_spoiler(self, fame_limit: float, *, by: int) -> float:
        if self.message.content.count("||") >= 2:
            return fame_limit + by
        return fame_limit

    def _penalise_channel(self, star_cfg: StarboardConfig, fame_limit: float, *, by: int) -> float:
        for pattern in star_cfg.channels.penalised:
            if isinstance(pattern, int) and self.channel.id == pattern:
                return fame_limit + by
            elif isinstance(pattern, str) and re.match(self.channel.name, pattern):
                return fame_limit + by
        return fame_limit

    async def is_already_in_starboard(self) -> bool:
        assert self.bot.user, "no user"
        if self.message.id in StarboardCog.bot_reactions_cache:
            return True

        for react in self.message.reactions:
            async for user in react.users():
                if user.id == self.bot.user.id:
                    return True
        return False

    def pick_starboard_channel(self) -> Tuple[Optional[Id], str]:
        assert (cfg := cast(GuildConfig, get(CONFIG.guilds, id=self.guild.id)))
        assert (star_cfg := cfg.channels.starboard)
        assert isinstance(self.message.channel, (discord.TextChannel, discord.Thread))
        assert self.bot.user, "no user"

        if self.message.channel.name == "memes":
            return star_cfg.best_of_memes, "best-of-memes"
        elif self.message.author.id == self.bot.user.id:
            return star_cfg.best_of_masaryk, "best-of-masaryk"
        else:
            return star_cfg.starboard, "starboard"


class StarboardEmbed(discord.Embed):
    def __init__(
        self,
        message: discord.Message,
        replies: List[str],
    ) -> None:
        super().__init__(color=0xFFDF00)

        assert isinstance(message.channel, (discord.TextChannel, discord.Thread))
        content = '\n'.join(replies)
        reactions = self._format_reactions(message)

        self.description = (
            f"{content}\n{reactions}\n" +
            f"[Jump to original!]({message.jump_url}) in {message.channel.mention}"
        )

        if message.author.avatar:
            self.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
        else:
            self.set_author(name=message.author.display_name, icon_url=message.author.default_avatar.url)

        if message.embeds:
            data = message.embeds[0]
            assert isinstance(data.url, str)
            if data.type == 'image' and not self.is_url_spoiler(message.content, data.url):
                self.set_image(url=data.url)

        if message.attachments:
            file = message.attachments[0]
            spoiler = file.is_spoiler()
            if not spoiler and file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                self.set_image(url=file.url)
            elif spoiler:
                self.add_field(name='Attachment',
                               value=f'||[{file.filename}]({file.url})||',
                               inline=False)
            else:
                self.add_field(name='Attachment',
                               value=f'[{file.filename}]({file.url})',
                               inline=False)

        cest = timezone(offset=timedelta(hours=+1))
        self.set_footer(text=message.created_at.astimezone(cest).strftime("%d.%m.%Y %H:%M"))

    def _format_reactions(self, message: discord.Message) -> str:
        return " ".join(
            self._format_reaction(reaction)
            for reaction in message.reactions
        )

    @staticmethod
    def _format_reaction(reaction: discord.Reaction) -> str:
        if isinstance(reaction.emoji, str):
            return f"{reaction} {reaction.count}"
        return f"<:{reaction.emoji.name}:{reaction.emoji.id}> {reaction.count}"

    @staticmethod
    def is_url_spoiler(text: str, url: str) -> bool:
        spoiler_regex = re.compile(r'\|\|(.+?)\|\|')
        spoilers = spoiler_regex.findall(text)
        for spoiler in spoilers:
            if url in spoiler:
                return True
            return False


class StarboardCog(commands.Cog):
    starred_messages: Dict[Id, deque[Id]] = {}
    bot_reactions_cache: deque[Id] = deque(maxlen=50)

    def __init__(self, bot: MasarykBOT, service: Optional[StarboardService] = None) -> None:
        self.bot = bot
        self.service = service or StarboardService(bot)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        assert self.bot.user, "no user"

        if CONFIG.bot.DEBUG:
            return

        if payload.user_id == self.bot.user.id:
            self.bot_reactions_cache.append(payload.message_id)

        try:
            message = await self.service.fetch_message(payload)
        except discord.NotFound:
            return

        if not (reaction := find(lambda r: payload.emoji.name == get_emoji_name(r.emoji), message.reactions)):
            return

        if not (context := self.service.construct_context(reaction)):
            return

        if not (starboard_channel := await self.service.process_starboard(context)):
            return

        replies = await self.service.get_reply_thread(message)
        embed = StarboardEmbed(message, replies)

        await starboard_channel.send(embed=embed)


async def setup(bot: MasarykBOT) -> None:
    await bot.add_cog(StarboardCog(bot))
