from discord import Message, Role, Emoji, PartialEmoji, File
from discord.ext import commands
from discord.utils import get

import logging
from typing import Union

from .utils import constants


log = logging.getLogger(__name__)


class UnicodeEmoji(commands.Converter):
    """
    discord.py's way of handling emojis is [Emoji, PartialEmoji, str]
    UnicodeEmoji accepts str only if it is present
    in UNICODE_EMOJI list
    """
    async def convert(self, ctx, argument):
        from emoji import UNICODE_EMOJI

        if isinstance(argument, list):
            for arg in argument:
                if arg not in UNICODE_EMOJI:
                    raise BadArgument('Emoji "{}" not found'.format(arg))
        else:
            if argument not in UNICODE_EMOJI:
                raise BadArgument('Emoji "{}" not found'.format(argument))
        
        return argument


Emote = Union[Emoji, PartialEmoji]


class Rolemenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def role(self, ctx):
        await ctx.send_help(ctx.command)

    @role.command()
    async def add(self, ctx, image_url: str, emoji: Emote, role: Role, *, text: str):
        if image := await self.get_image_from_url(image_url):
            await ctx.send(file=image)
        
        message = await ctx.send(f"**{text.strip().strip('*')}**")

        msg_data = await self.bot.db.messages.prepare(message)
        await self.bot.db.messages.insert(msg_data)

        menu_data = await self.bot.db.rolemenu.prepare(message, role, emoji)
        await self.bot.db.rolemenu.insert(menu_data)
        
        await message.add_reaction(emoji)
        await ctx.message.delete()

    @staticmethod
    async def get_image_from_url(url):
        import io
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = io.BytesIO(await resp.read())
                return File(data, 'image.png')


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.on_raw_reaction_update(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.on_raw_reaction_update(payload)

    async def on_raw_reaction_update(self, payload):
        if payload.channel_id not in constants.about_you_channels:
            return
        
        row = await self.bot.db.rolemenu.select(payload.message_id)

        guild = self.bot.get_guild(payload.guild_id)
        role = get(guild.roles, id=row["role_id"])
        if not role:
            return

        author = guild.get_member(payload.user_id)

        if payload.event_type == "REACTION_ADD":
            await author.add_roles(role)
            log.info(f"added role {str(role)} to {author}")
        else:
            await author.remove_roles(role)
            log.info(f"removed role {str(role)} to {author}")


    @commands.Cog.listener()
    async def on_ready(self):
        for channel_id in constants.about_you_channels:
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                continue

            async for message in channel.history():
                if not message.reactions:
                    continue
                    
                row = await self.bot.db.rolemenu.select(message.id)
                if row is None:
                    log.warn(f"reactions on message {message.id} in {channel} ({channel.guild}) are not in the database")
                    continue

                role = get(channel.guild.roles, id=row["role_id"])
                if role is None:
                    log.warn(f"role on message {message.id} in {channel} ({channel.guild}) does not exist")
                    continue

                async for user in message.reactions[0].users():
                    has_role = get(user.roles, id=role.id)
                    if not has_role:
                        log.info(f"added role {str(role)} to {user}")
                        await user.add_roles(role)

                for user in role.members:
                    has_reacted = await message.reactions[0].users().get(id=user.id)
                    if not has_reacted:
                        log.info(f"removed role {str(role)} to {user}")
                        await user.remove_roles(role)

                    




def setup(bot):
    bot.add_cog(Rolemenu(bot))
