import discord
from discord.ext import commands
from discord.ext.commands import Greedy, Converter
from discord import Color, Embed, Member, File, Role, Emoji, PartialEmoji

import core.utils.get
from core.utils.db import Database
from core.utils.checks import needs_database, safe

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


class Aboutmenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.imagePath = "https://gitlab.com/zloutek1/MasarykBOT/raw/develop/bot/assets/"

    @commands.group(name="aboutmenu")
    async def aboutmenu(self, ctx):
        pass

    @aboutmenu.command(name="create", aliases=("add",))
    @needs_database
    async def aboutmenu_create(self, ctx, image_path: str,
                               roles: Greedy[Role],
                               emojis: Greedy[Union[Emoji, PartialEmoji, UnicodeEmoji]],
                               *, text: str, db=Database()):

        if not os.path.isfile("assets/" + image_path):
            await safe(ctx.message.delete)(delay=5)
            await ctx.send("`Invalid file path`", delete_after=5)
            return

        if len(roles) != len(emojis):
            await safe(ctx.message.delete)(delay=5)
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
                    (menu_id, emoji, role_id)
                VALUES
                    (%s, %s, %s)
            """, (menu_id, str(emoji), role.id))
        await db.commit()

        await safe(ctx.message.delete)()

    """---------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def on_raw_reaction_update(self, payload, event_type: str, db=Database()):
        # reacted in aboutmenu channel?
        await db.execute("""
            SELECT * FROM aboutmenu
            WHERE channel_id = %s AND deleted_at IS NULL
            LIMIT 1
        """, (payload.channel_id,))
        if not await db.fetchone():
            return

        # does the option exist? get it
        await db.execute("""
            SELECT channel_id, message_id, image, `text`, emoji, role_id
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
        role = core.utils.get(guild.roles, id=row["role_id"])
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

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.on_raw_reaction_update(payload, event_type="REACTION_REMOVE")

    """---------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_ready(self, *, db=Database()):
        self.bot.readyCogs[self.__class__.__name__] = False

        await db.execute("""
            SELECT * FROM aboutmenu
            WHERE deleted_at IS NULL
        """)
        rows = await db.fetchall()

        # check each message
        channels = {}
        for row in rows:
            # cache channel or get the channel
            channel_id = row["channel_id"]
            if channels.get(channel_id) is None:
                channels[channel_id] = self.bot.get_channel(channel_id)
            channel = channels.get(channel_id)

            # get the message
            message = await channel.fetch_message(row["message_id"])
            if message is None:
                print("Message does not exist in aboutmenu")
                continue

            # get reactions
            for reaction in message.reactions:
                await db.execute("""
                    SELECT * FROM aboutmenu_options
                    WHERE menu_id = %s AND emoji = %s AND deleted_at is NULL
                """, (row["id"], str(reaction)))
                react_db = await db.fetchone()

                # get the role
                role = channel.guild.get_role(react_db["role_id"])

                new_reacted = set(await reaction.users().flatten())
                old_reacted = set(role.members)

                # get the difference
                to_add = new_reacted - old_reacted
                to_remove = old_reacted - new_reacted

                # balance the difference
                for member in to_add:
                    await member.add_roles(role)

                for member in to_remove:
                    await member.remove_roles(role)

        self.bot.readyCogs[self.__class__.__name__] = True


def setup(bot):
    bot.add_cog(Aboutmenu(bot))
