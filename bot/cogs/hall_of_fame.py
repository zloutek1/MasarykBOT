from discord import Embed
from discord.ext import commands
from discord.utils import get

from .utils import constants


class HoF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.count < constants.fame_react_limit:
            return

        message = reaction.message
        guild = message.guild
        
        if message.channel.id in (constants.verification_channels + constants.about_you_channels):
            return

        channel = get(guild.text_channels, name="starboard")
        if channel is None:
            channel = await guild.create_text_channel("starboard")

        embed = self.get_embed(message)

        messages = await channel.history().flatten()
        for message in messages:
            for em in message.embeds:
                if em.description.split('\n')[-1] == embed.description.split('\n')[-1]:
                    return 

        await channel.send(embed=embed)

    @staticmethod
    def get_embed(message):
        embed = Embed(
            description=f"{message.content}\n" +
                        " ".join(f"{r.count} <:{r.emoji.name}:{r.emoji.id}>" if r.custom_emoji else f"{r.count} {r}" 
                                 for r in message.reactions) + '\n' +
                        f"[Jump to original!]({message.jump_url}) in {message.channel.mention}",
            color=0xFFDF00)

        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url_as(format='png'))

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
                embed.add_field(name='Attachment', value=f'||[{file.filename}]({file.url})||', inline=False)
            else:
                embed.add_field(name='Attachment', value=f'[{file.filename}]({file.url})', inline=False)

        return embed

def setup(bot):
    bot.add_cog(HoF(bot))