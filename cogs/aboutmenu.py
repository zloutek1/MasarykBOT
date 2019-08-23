import discord
from discord.ext import commands
from discord.ext.commands import Greedy, Converter
from discord import Color, Embed, Member, File, Role, Emoji, PartialEmoji

import core.utils.get
from core.utils.db import Database
from core.utils.checks import needs_database

import os
from typing import Union
from emoji import UNICODE_EMOJI
from datetime import datetime, timedelta


class UnicodeEmoji(Converter):
    async def convert(self, ctx, argument):
        if isinstance(argument, list):
            for arg in argument:
                if arg not in UNICODE_EMOJI:
                    raise BadArgument('Emoji "{}" not found'.format(arg))
        else:
            if argument not in UNICODE_EMOJI:
                raise BadArgument('Emoji "{}" not found'.format(argument))
        return argument


class AboutMenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.imagePath = "https://gitlab.com/zloutek1/MasarykBOT/raw/master/"

    @commands.group(name="aboutmenu")
    async def aboutmenu(self, ctx):
        pass

    @aboutmenu.command(name="create", aliases=("add",))
    @needs_database
    async def aboutmenu_create(self, ctx, image_path: str, roles: Greedy[Role], emojis: Greedy[Union[Emoji, PartialEmoji, UnicodeEmoji]], *, text: str, db=Database()):
        if not os.path.isfile(image_path):
            await ctx.send("`Invalid file path`", delete_after=5)
            return

        if len(roles) != len(emojis):
            await ctx.send("`len(roles) != len(emojis)`", delete_after=5)
            return

        await ctx.channel.set_permissions(self.bot.user,
            add_reactions=True, send_messages=True)
        await ctx.channel.set_permissions(ctx.guild.default_role,
            add_reactions=False, send_messages=False)

        embed = Embed(title=text)
        embed.set_image(url=os.path.join(self.imagePath, image_path))
        message = await ctx.send(embed=embed)

        for emoji in emojis:
            self.bot.loop.create_task(message.add_reaction(emoji))

        await db.execute("""
            INSERT INTO aboutmenu
                (channel_id, message_id, image, `text`)
            VALUES
                (%s, %s, %s, %s)
        """, (ctx.channel.id, message.id, os.path.join(self.imagePath, image_path), text))
        await db.commit()

        await db.execute("SELECT LAST_INSERT_ID() AS last_id")
        result = await db.fetchone()
        if not result:
            return

        menu_id = result["last_id"]

        for emoji, role in zip(emojis, roles):
            await db.execute("""
                INSERT INTO aboutmenu_options
                    (menu_id, emoji, role)
                VALUES
                    (%s, %s, %s)
            """, (menu_id, str(emoji), str(role)))
        await db.commit()

        await ctx.message.delete()

    """---------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def on_raw_reaction_update(self, payload, event_type: str, db=Database()):
        # does the option exist? get it
        await db.execute("""
            SELECT channel_id, message_id, image, `text`, emoji, role
            FROM aboutmenu
            INNER JOIN aboutmenu_options AS opt
            ON aboutmenu.id = opt.menu_id
            WHERE message_id = %s AND emoji = %s AND aboutmenu.deleted_at IS NULL AND opt.deleted_at IS NULL
            LIMIT 1
        """, (payload.message_id, str(payload.emoji)))
        row = await db.fetchone()
        if not row:
            return

        # get role
        guild = self.bot.get_guild(payload.guild_id)
        text = row["role"]
        role = core.utils.get(guild.roles, name=text)
        if not role:
            return

        author = guild.get_member(payload.user_id)
        if event_type == "REACTION_ADD":
            await author.add_roles(role)
        else:
            await author.remove_roles(role)

    """---------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.on_raw_reaction_update(payload, event_type="REACTION_ADD")

    """---------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.on_raw_reaction_update(payload, event_type="REACTION_REMOVE")


def setup(bot):
    bot.add_cog(AboutMenu(bot))
