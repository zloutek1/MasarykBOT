import logging
import math
import re
from collections import deque
from datetime import timedelta, timezone
from textwrap import dedent
from typing import Any, Dict, List, Optional, Tuple, cast

from bot.constants import Config
from disnake import (Embed, Emoji, Guild, Message, PartialEmoji,
                     RawReactionActionEvent, Reaction, TextChannel, Thread)
from disnake.errors import NotFound
from disnake.ext import commands
from disnake.utils import find, get
from emoji import demojize

from .utils.context import Context

log = logging.getLogger(__name__)
Id = int


class Starboard(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        self.starred_messages: Dict[Id, deque[Id]] = {}

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent) -> None:
        if (channel := self.bot.get_channel(payload.channel_id)) is None:
            return

        if not isinstance(channel, (TextChannel, Thread)):
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except NotFound:
            log.warn(f"message with id {payload.message_id} in channel {channel} not found")
            return

        if reaction := self.lookup_reaction(payload.emoji, message.reactions):
            await self.process_starboard(reaction)

    @staticmethod
    def lookup_reaction(emoji: PartialEmoji, reactions: List[Reaction]) -> Optional[Reaction]:
        def react_emoji_name(reaction: Reaction) -> str:
            if isinstance(reaction.emoji, str):
                return reaction.emoji
            return reaction.emoji.name

        return find(lambda r: emoji.name == react_emoji_name(r), reactions)

    async def process_starboard(self, reaction: Reaction) -> None:
        message = reaction.message
        channel = message.channel
        guild = message.guild

        assert isinstance(channel, (TextChannel, Thread))
        assert guild is not None, "Starboard can only run inside a guild"

        if (guild_config := get(Config.guilds, id=guild.id)) is None:
            return

        if (self.is_recently_starred(message) or
            await self.is_already_in_starboard(message) or
            channel.name == "starboard" or
            message.channel.id in guild_config.channels or
            reaction.count < guild_config.STARBOARD_REACT_LIMIT or
            reaction.count < self.calculate_ignore_score(reaction)):

            log.debug("message with %s(%s) reactions found (%s, %s, %s)",
                      reaction.emoji, reaction.count, guild, channel, message.id)
            return

        log.info("adding message with %s reactions to starboard (%s, %s, %s)",
                 reaction.count, guild, channel, message.id)

        self.starred_messages.setdefault(guild.id, deque(maxlen=50))
        self.starred_messages[guild.id].append(message.id)

        await message.add_reaction(reaction.emoji)

        (channel_id, channel_name) = self.pick_target_starboard_channel(message, guild_config)
        starboard_channel = await self.get_or_create_channel(guild, channel_id, channel_name)

        await starboard_channel.send(embed=await self.get_embed(message))

    def is_recently_starred(self, message: Message) -> bool:
        return (message.guild is not None and
                message.guild.id in self.starred_messages and
                message.id in self.starred_messages[message.guild.id])

    async def is_already_in_starboard(self, message: Message) -> bool:
        for react in message.reactions:
            if await react.users().get(id=self.bot.user.id) is not None:
                return True
        return False

    def pick_target_starboard_channel(
        self,
        message: Message,
        guild_config: Any
    ) -> Tuple[Id, str]:
        assert isinstance(message.channel, (TextChannel, Thread))

        if message.channel.name == "memes":
            return (guild_config.channels.best_of_memes, "best-of-memes")
        elif message.author.id == self.bot.user.id:
            return (guild_config.channels.best_of_masaryk, "best-of-masaryk")
        else:
            return (guild_config.channels.starboard, "starboard")


    async def get_or_create_channel(
        self,
        guild: Guild,
        existing_id: Optional[Id],
        name: Optional[str]
    ) -> TextChannel:

        channel = get(guild.text_channels, id=existing_id)
        if channel is None:
            channel = get(guild.text_channels, name=name)
        if channel is None:
            assert name
            channel = await guild.create_text_channel(name)
        return channel


    @staticmethod
    def calculate_ignore_score(reaction: Reaction) -> float:
        message = reaction.message
        channel = message.channel
        guild = message.guild

        assert isinstance(channel, (TextChannel, Thread))
        assert guild is not None, "Starboard can only run inside a guild"

        emoji_name = (emoji.name
                      if isinstance(emoji := reaction.emoji, (Emoji, PartialEmoji)) else
                      demojize(emoji))
        msg_content = message.content

        guild_config = get(cast(List[Any], Config.guilds), id=guild.id)
        assert guild_config is not None, f"ERROR: missing guild config for guild with id {guild.id}"

        fame_limit = cast(int, guild_config.STARBOARD_REACT_LIMIT)
        if len(channel.members) > 100:
            fame_limit += 10

        ignored_rooms = ['cute', 'fame', 'best-of-memes', 'newcomers', 'fetish']
        if any(map(lambda ignored_pattern: ignored_pattern in channel.name.lower(), ignored_rooms)):
            return math.inf

        common_rooms = ['memes']
        if any(map(lambda common_pattern: common_pattern in channel.name.lower(), common_rooms)):
            fame_limit += 15

        if msg_content.startswith("||") and msg_content.endswith("||"):
            fame_limit += 5

        blocked_reactions = ['_wine']
        for blocked_pattern in blocked_reactions:
            if blocked_pattern in emoji_name.lower():
                return math.inf

        common_reactions = ['kek', 'pepe', 'lul', 'lol', 'pog', 'peepo', 'ano', 'no', 'yes', 'no', 'cringe']
        if any(map(lambda common_pattern: common_pattern in emoji_name.lower(), common_reactions)):
            fame_limit += 5

        if "star" in emoji_name:
            return fame_limit - 5
        return fame_limit

    async def get_embed(self, message: Message) -> Embed:
        def format_reaction(react: Reaction) -> str:
            emoji = react.emoji
            if not isinstance(emoji, str):
                return f"{react.count} <:{emoji.name}:{emoji.id}>"
            else:
                return f"{react.count} {react}"

        reply_emoji = get(self.bot.emojis, name="reply")

        async def get_reply_thread(message: Message, depth: int = 15) -> List[str]:
            if not message.reference or not message.reference.message_id:
                return []
            if depth <= 0:
                return [f"{reply_emoji} [truncated]"]

            reply = await message.channel.fetch_message(message.reference.message_id)
            replies = await get_reply_thread(reply, depth-1)

            replies.append(f"{reply_emoji} {reply.content}" if replies else reply.content)
            return replies

        reactions = " ".join(format_reaction(react) for react in message.reactions)

        total_length = len(message.content) + len(reactions)
        reply_thread = await get_reply_thread(message)
        skipped = 0
        while len(reply_thread) > 0 and total_length + sum(map(len, reply_thread)) > 1200:
            reply_thread.pop()
            skipped += 1
        for _ in range(skipped):
            reply_thread.append(f"{reply_emoji} [Reply too long to render]")

        replies = '\n'.join(reply_thread) + "\n"
        replies += str(reply_emoji) if message.reference else ''

        assert isinstance(message.channel, (TextChannel, Thread))
        embed = Embed(
            description=f"{replies}{message.content}\n{reactions}\n" +
                        f"[Jump to original!]({message.jump_url}) in {message.channel.mention}",
            color=0xFFDF00)

        embed.set_author(name=message.author.display_name,
                         icon_url=message.author.avatar and message.author.avatar.with_format('png').url)

        CEST = timezone(offset=timedelta(hours=+2))
        embed.set_footer(text=message.created_at.astimezone(CEST).strftime("%d.%m.%Y %H:%M"))

        if message.embeds:
            data = message.embeds[0]
            assert isinstance(data.url, str)
            if data.type == 'image' and not self.is_url_spoiler(message.content, data.url):
                embed.set_image(url=data.url)

        if message.attachments:
            file = message.attachments[0]
            spoiler = file.is_spoiler()
            if not spoiler and file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                embed.set_image(url=file.url)
            elif spoiler:
                embed.add_field(name='Attachment',
                                value=f'||[{file.filename}]({file.url})||',
                                inline=False)
            else:
                embed.add_field(name='Attachment',
                                value=f'[{file.filename}]({file.url})',
                                inline=False)

        return embed

    @staticmethod
    def is_url_spoiler(text: str, url: str) -> bool:
        spoiler_regex = re.compile(r'\|\|(.+?)\|\|')
        spoilers = spoiler_regex.findall(text)
        for spoiler in spoilers:
            if url in spoiler:
                return True
        return False

    @commands.command()
    async def starboard(self, ctx: Context, channel: TextChannel, message_id: int) -> None:
        try:
            message = await channel.fetch_message(message_id)
        except NotFound :
            await ctx.send_error("Message not found")
            return

        starscore = '\n        '.join(
                        f"`{r.count} / {self.calculate_ignore_score(r)}` {r.emoji}" for r in message.reactions)

        result = dedent(f"""
        **author**: {message.author}
        **content**[{len(message.content)}]: {message.jump_url}
        **reactions**[{len(message.reactions)}]: {[(str(r), r.count) for r in message.reactions]}
        **attachments**[{len(message.attachments)}]: {message.attachments}
        **embeds**[{len(message.embeds)}]: {message.embeds}

        **starboard score**:
        {starscore}
        """)

        await ctx.send(result)

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Starboard(bot))
