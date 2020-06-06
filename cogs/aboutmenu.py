from discord.ext import commands
from discord.ext.commands import Greedy, Converter, BadArgument, has_permissions
from discord import Embed, Role, Emoji, PartialEmoji, Member

import core.utils.get
from core.utils.db import Database
from core.utils.checks import needs_database, safe

import os
import logging
from typing import Union
from emoji import UNICODE_EMOJI


class UnicodeEmoji(Converter):
    """
    discord.py's way of handling emojis is [Emoji, PartialEmoji, str]
    UnicodeEmoji accepts str only if it is present
    in UNICODE_EMOJI list
    """
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
        self.log = logging.getLogger(__name__)
        self.imagePath = "https://gitlab.com/zloutek1/MasarykBOT/raw/develop/bot/assets/"

    @commands.group(name="aboutmenu")
    @has_permissions(administrator=True)
    async def aboutmenu(self, ctx):
        pass

    @aboutmenu.command()
    @needs_database
    async def remove_user(self, ctx, member: Member, *, db: Database):
        """
        remove every reaction from user
        in #about-menu channels
        """

        await db.execute("SELECT * FROM aboutmenu")
        menus = await db.fetchall()

        for menu in menus:
            channel = self.bot.get_channel(menu["channel_id"])
            if not channel:
                continue

            message = await channel.fetch_message(menu["message_id"])
            if not message:
                continue

            for reaction in message.reactions:
                await message.remove_reaction(reaction, member)

    @aboutmenu.command(name="create", aliases=("add",))
    @needs_database
    @has_permissions(administrator=True)
    async def aboutmenu_create(self, ctx, image_path: str,
                               roles: Greedy[Role],
                               emojis: Greedy[Union[Emoji, PartialEmoji, UnicodeEmoji]],
                               *, text: str, db: Database = None):
        """
        create about-menu in current channel
        @param image_path - path to github/develop/assets/image.ext
        @param roles - list of discord roles
        @param emojis - list of discord emojis
        @param text - text to display in embed

        ensure the len(roles) == len(emojis)
        disable users to send messages in this channel
        send an embed with the image
        add aboutmenu into database
        """

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
    async def on_raw_reaction_update(self, payload, event_type: str, db: Database = None):
        """
        check if user clicked on emoji in aboutmenu channel
        find option in the database, fetch the discord objects
        add/remove user the corresponding role
        """
        # reacted in aboutmenu channel?
        await db.execute("""
            SELECT * FROM aboutmenu
            INNER JOIN channel ON channel.id = channel_id
            WHERE guild_id = %s AND channel_id = %s AND aboutmenu.deleted_at IS NULL
            LIMIT 1
        """, (payload.guild_id, payload.channel_id))
        if not await db.fetchone():
            return
        guild = self.bot.get_guild(payload.guild_id)
        author = guild.get_member(payload.user_id)
        self.log.info(f"{event_type}: {str(payload.emoji)} for {author}")

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
        self.log.info("found the clicked option in database")

        # get role
        role = core.utils.get(guild.roles, id=row["role_id"])
        if not role:
            return
        self.log.info("got the role object from discord")

        if event_type == "REACTION_ADD":
            await author.add_roles(role)
        else:
            await author.remove_roles(role)
        self.log.info(f"added / removed role to {author} successfully")

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
    async def on_ready(self, *, db: Database = None):
        """
        for each aboutmenu
        if the channel does not exist, mark the aboutmenu as deleted
        for each option in aboutmenu
            get the difference of reactors vs users with the role
            add/remove users to balance the differences
        """

        self.bot.readyCogs[self.__class__.__name__] = False

        self.log.info("Catching up aboutmenu")

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
            if channel is None:
                # channel does not exist, skip
                continue
            self.log.info(f"Catching up channel {channel}")

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
                if role is None:
                    print("role", react_db["role_id"], "for", row["id"], "not found")
                    continue

                new_reacted = set(await reaction.users().flatten())
                old_reacted = set(role.members)

                # get the difference
                to_add = new_reacted - old_reacted
                to_remove = old_reacted - new_reacted

                # balance the difference
                for user in to_add:
                    member = core.utils.get(channel.guild.members, id=user.id)
                    if member:
                        member_student_role = core.utils.get(
                            member.roles, name="Student")
                        if member_student_role:
                            await member.add_roles(role)

                for user in to_remove:
                    member = core.utils.get(channel.guild.members, id=user.id)
                    if member:
                        await member.remove_roles(role)

        self.log.info(f"caught up aboutmenu")

        self.bot.readyCogs[self.__class__.__name__] = True


def setup(bot):
    bot.add_cog(Aboutmenu(bot))
