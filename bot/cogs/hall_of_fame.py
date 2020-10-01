import re

from discord import Embed
from discord.ext import commands
from discord.utils import get

from .utils import constants


class HoF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, _user):
        if reaction.count < constants.FAME_REACT_LIMIT:
            return

        blocked_reactions = [r'.*brandejs_wine.*']
        for blocked_pattern in blocked_reactions:
            if re.match(blocked_pattern, reaction.name.lower()) is not None:
                return

        common_reactions = [r'.*kek.*', r'.*pepe.*', r'.*lul.*', r'.*lol.*', r'.*peepo.*']
        for common_pattern in common_reactions:
            if re.match(common_pattern, reaction.name.lower()) is not None:
                if reaction.count < constants.FAME_REACT_LIMIT + 5:
                    return

        message = reaction.message
        guild = message.guild

        if message.channel.id in constants.verification_channels + constants.about_you_channels:
            return

        channel = get(guild.text_channels, name="starboard")
        if channel is None:
            channel = await guild.create_text_channel("starboard")

        new_embed = self.get_embed(message)

        messages = await channel.history().flatten()
        for message in messages:
            for embed in message.embeds:
                if embed.description.split('\n')[-1] == new_embed.description.split('\n')[-1]:
                    await message.edit(embed=new_embed)
                    return

        await channel.send(embed=new_embed)

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
    bot.add_cog(HoF(bot))
