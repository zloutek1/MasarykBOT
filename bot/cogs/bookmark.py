import discord
from discord import (Message, RawReactionActionEvent, PartialEmoji, Embed, DMChannel)
from discord.abc import Messageable, GuildChannel
from discord.ext import commands


class BookmarkService:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    def is_bookmark_emoji(emoji: PartialEmoji) -> bool:
        if not emoji.is_unicode_emoji():
            return False
        return emoji.name in '🔖'

    @staticmethod
    def is_delete_emoji(emoji: PartialEmoji) -> bool:
        if not emoji.is_unicode_emoji():
            return False
        return emoji.name in '🗑️'

    @staticmethod
    def is_bookmark_message(message: Message) -> bool:
        if not isinstance(message.channel, DMChannel):
            return False

        if not message.author.bot or len(message.embeds) != 1:
            return False

        embed = message.embeds[0]
        if not embed.title or not embed.title.startswith("You have pinned a message"):
            return False
        return True

    async def fetch_message(self, payload: RawReactionActionEvent) -> Message:
        channel = await self.bot.fetch_channel(payload.channel_id)
        if not isinstance(channel, Messageable):
            raise AssertionError(f"cannot send messages in channel {channel}")
        return await channel.fetch_message(payload.message_id)

    @staticmethod
    def to_embed(message: Message) -> Embed:
        if not isinstance(message.channel, GuildChannel):
            raise AssertionError(f"channel {message.channel} is not a guild channel")

        embed = Embed(
            title=f"You have pinned a message in {message.guild}",
            description=f"{message.content}\n\n" +
                        f"[Jump to original!]({message.jump_url}) in {message.channel.mention}",
            color=0xFFDF00
        )

        embed.set_author(
            name=message.author.display_name,
            icon_url=(message.author.default_avatar.url
                      if message.author.avatar is None else
                      message.author.avatar.url))

        embed.set_footer(
            text="react on this  message with 🗑️ to delete"
        )

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
                embed.add_field(
                    name='Attachment',
                    value=f'||[{file.filename}]({file.url})||',
                    inline=False
                )
            else:
                embed.add_field(
                    name='Attachment',
                    value=f'[{file.filename}]({file.url})',
                    inline=False
                )

        return embed


class Bookmark(commands.Cog):
    def __init__(self, bot: commands.Bot, service: BookmarkService = None) -> None:
        self.bot = bot
        self.service = service or BookmarkService(bot)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent) -> None:
        if self.service.is_bookmark_emoji(payload.emoji):
            return await self.on_bookmark_reaction(payload)

        if self.service.is_delete_emoji(payload.emoji):
            return await self.on_delete_reaction(payload)

    async def on_bookmark_reaction(self, payload: RawReactionActionEvent) -> None:
        try:
            message = await self.service.fetch_message(payload)
        except discord.NotFound:
            return

        user = await self.bot.fetch_user(payload.user_id)
        embed = self.service.to_embed(message)
        await user.send(embed=embed)

    async def on_delete_reaction(self, payload: RawReactionActionEvent) -> None:
        try:
            message = await self.service.fetch_message(payload)
        except discord.NotFound:
            return
        if not self.service.is_bookmark_message(message):
            return
        await message.delete()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bookmark(bot))
