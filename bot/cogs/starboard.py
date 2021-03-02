import re
from emoji import demojize
import logging

from discord import Embed, Emoji, PartialEmoji
from discord.ext import commands
from discord.utils import get

from bot.constants import Config

log = logging.getLogger(__name__)

class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, _user):
        guild_config = get(Config.guilds, id=reaction.message.guild.id)

        if reaction.count < guild_config.STARBOARD_REACT_LIMIT:
            return

        message = reaction.message
        channel = message.channel
        guild = message.guild

        log.info("message with %s reactions found (%s)", reaction.count, guild)

        if channel.name == "starboard" or channel.id == guild_config.channels.starboard:
            return

        if self.should_ignore(reaction):
            return

        if message.channel.id in [guild_config.channels.verification, guild_config.channels.about_you]:
            return

        new_embed = self.get_embed(message)

        channel = await self.get_startobard_channel(guild)
        messages = await channel.history().flatten()
        for message in messages:
            for embed in message.embeds:
                if embed.description.split('\n')[-1] == new_embed.description.split('\n')[-1]:
                    await message.edit(embed=new_embed)
                    return

        await channel.send(embed=new_embed)

    async def get_startobard_channel(self, guild):
        guild_config = get(Config.guilds, id=guild.id)
        channel = get(guild.text_channels, id=guild_config.channels.starboard)
        if channel is None:
            channel = get(guild.text_channels, name="starboard")
        if channel is None:
            channel = await guild.create_text_channel("starboard")
        return channel

    @staticmethod
    def should_ignore(reaction):
        channel = reaction.message.channel
        emoji_name = emoji.name if isinstance(emoji := reaction.emoji, Emoji) or isinstance(emoji, PartialEmoji) else demojize(emoji)
        msg_content = reaction.message.content

        guild_config = get(Config.guilds, id=reaction.message.guild.id)
        fame_limit = guild_config.STARBOARD_REACT_LIMIT
        if len(channel.members) > 100:
            fame_limit += 10

        ignored_rooms = ['cute', 'fame']
        if any(map(lambda ignored_pattern: ignored_pattern in channel.name.lower(), ignored_rooms)):
            return True

        common_rooms = ['memes']
        if any(map(lambda common_pattern: common_pattern in channel.name.lower(), common_rooms)):
            fame_limit += 15

        if msg_content.startswith("||") and msg_content.endswith("||"):
            fame_limit += 5

        blocked_reactions = ['_wine']
        for blocked_pattern in blocked_reactions:
            if blocked_pattern in emoji_name.lower():
                return True

        common_reactions = ['kek', 'pepe', 'lul', 'lol', 'pog', 'peepo', 'ano', 'no', 'yes', 'no', 'cringe']
        if any(map(lambda common_pattern: common_pattern in emoji_name.lower(), common_reactions)):
            fame_limit += 5

        if "star" in emoji_name and reaction.count < fame_limit - 5:
            return False

        if reaction.count < fame_limit:
            return True

        return False

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

def setup(bot):
    bot.add_cog(Starboard(bot))
