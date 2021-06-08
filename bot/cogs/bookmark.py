from discord import Embed, DMChannel
from discord.ext import commands
from discord.utils import find


class Bookmark(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        user = await channel.guild.fetch_member(payload.user_id)
        message = await channel.fetch_message(payload.message_id)
        reaction = find(lambda r: payload.emoji.name == (r.emoji if isinstance(r.emoji, str) else r.emoji.name), message.reactions)

        if not isinstance(reaction.emoji, str):
            return

        if reaction.emoji not in ('🔖'):
            return

        embed = self.get_embed(reaction.message)
        message = await user.send(embed=embed)

    def get_embed(self, message):
        embed = Embed(
            title=f"You have pinned a message in {message.guild}",
            description=f"{message.content}\n" +
                        f"[Jump to original!]({message.jump_url}) in {message.channel}",
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

def setup(bot):
    bot.add_cog(Bookmark(bot))
