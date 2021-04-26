import re
import math
from emoji import demojize
import logging
from collections import deque
from textwrap import dedent

from discord import Embed, Emoji, PartialEmoji, TextChannel
from discord.ext import commands
from discord.utils import get, find

from bot.constants import Config

log = logging.getLogger(__name__)

class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.known_messages = deque(maxlen=30)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        reaction = find(lambda r: payload.emoji.name == (r.emoji if isinstance(r.emoji, str) else r.emoji.name), message.reactions)
        await self.process_starboard(reaction)

    async def process_starboard(self, reaction):
        if reaction.message.id in self.known_messages:
            return

        if (guild_config := get(Config.guilds, id=reaction.message.guild.id)) is None:
            return
        if reaction.count < guild_config.STARBOARD_REACT_LIMIT:
            return

        message = reaction.message
        channel = message.channel
        guild = message.guild

        log.info("message with %s reactions found (%s)", reaction.count, guild)

        if channel.name == "starboard" or channel.id == guild_config.channels.starboard:
            return

        if reaction.count < self.calculate_ignore_score(reaction):
            return

        if message.channel.id in [guild_config.channels.verification, guild_config.channels.about_you]:
            return

        self.known_messages.append(message.id)

        for reaction in message.reactions:
            if await reaction.users().get(id=self.bot.user.id) is not None:
                return

        await message.add_reaction(reaction.emoji)

        if channel.name == "memes":
            memes_channel = await self.get_or_create_channel(guild, guild_config.channels.best_of_memes, "best-of-memes")
            await memes_channel.send(embed=self.get_embed(message))

        starboard_channel = await self.get_or_create_channel(guild, guild_config.channels.starboard, "starboard")
        await starboard_channel.send(embed=self.get_embed(message))

    async def get_or_create_channel(self, guild, existing_id=None, name=None):
        channel = get(guild.text_channels, id=existing_id)
        if channel is None:
            channel = get(guild.text_channels, name=name)
        if channel is None:
            channel = await guild.create_text_channel(name)
        return channel

    @staticmethod
    def calculate_ignore_score(reaction):
        channel = reaction.message.channel
        emoji_name = emoji.name if isinstance(emoji := reaction.emoji, Emoji) or isinstance(emoji, PartialEmoji) else demojize(emoji)
        msg_content = reaction.message.content

        guild_config = get(Config.guilds, id=reaction.message.guild.id)
        fame_limit = guild_config.STARBOARD_REACT_LIMIT
        if len(channel.members) > 100:
            fame_limit += 10

        ignored_rooms = ['cute', 'fame']
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

    def get_embed(self, message):
        def format_reaction(react):
            emoji = react.emoji
            if react.custom_emoji:
                return f"{react.count} <:{emoji.name}:{emoji.id}>"
            else:
                return f"{react.count} {react}"

        reactions = " ".join(format_reaction(react) for react in message.reactions)

        embed = Embed(
            description=f"{message.content}\n{reactions}\n" +
                        f"[Jump to original!]({message.jump_url}) in {message.channel.mention}",
            color=0xFFDF00)

        embed.set_author(name=message.author.display_name,
                         icon_url=message.author.avatar_url_as(format='png'))

        if message.embeds:
            data = message.embeds[0]
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
    def is_url_spoiler(text, url):
        spoiler_regex = re.compile(r'\|\|(.+?)\|\|')
        spoilers = spoiler_regex.findall(text)
        for spoiler in spoilers:
            if url in spoiler:
                return True
        return False

    @commands.command()
    async def starboard(self, ctx, channel: TextChannel, message_id: int):
        message = await channel.fetch_message(message_id)

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

def setup(bot):
    bot.add_cog(Starboard(bot))
