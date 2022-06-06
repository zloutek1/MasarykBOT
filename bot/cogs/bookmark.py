from threading import Thread

from disnake import (ApplicationCommandInteraction, Embed, Member, Message,
                     RawReactionActionEvent, TextChannel)
from disnake.errors import NotFound
from disnake.ext import commands


class Bookmark(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent) -> None:
        if not payload.emoji.is_unicode_emoji():
            return

        if payload.emoji.name not in ('🔖'):
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not isinstance(channel, (TextChannel, Thread)):
            return

        user = await channel.guild.fetch_member(payload.user_id)

        try:
            message = await channel.fetch_message(payload.message_id)
        except NotFound as ex:
            await channel.send(f"{user.mention} [Error]: {ex.text}")
            return

        embed = self.get_embed(message)
        await user.send(embed=embed)


    @commands.message_command(guild_ids=[486184376544002073, 573528762843660299])
    async def bookmark(self, inter: ApplicationCommandInteraction, message: Message) -> None:
        embed = self.get_embed(message)
        await inter.author.send(embed=embed)

    def get_embed(self, message: Message) -> Embed:
        embed = Embed(
            title=f"You have pinned a message in {message.guild}",
            description=f"{message.content}\n" +
                        f"[Jump to original!]({message.jump_url}) in {message.channel}",
            color=0xFFDF00)

        embed.set_author(name=message.author.display_name,
                         icon_url=(message.author.default_avatar.url if message.author.avatar is None else
                                   message.author.avatar.with_format('png').url))


        if message.embeds:
            data = message.embeds[0]
            if data.type == 'image':
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

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Bookmark(bot))
