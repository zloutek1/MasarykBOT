import asyncio
import logging

from discord import Colour, Embed, Member, Object, File
import discord.utils
from discord.ext import commands
from discord.ext.commands import Bot, Converter, group, Context, has_permissions

from config import BotConfig

from PIL import Image, ImageDraw, ImageFont
import os
import json
import re

import core.utils.get
from core.utils.db import Database
from core.utils.checks import needs_database


class ReactionPicker(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.log = logging.getLogger(__name__)

    """--------------------------------------------------------------------------------------------------------------------------"""

    @group(name='reactionmenu', aliases=('rolemenu', 'rlm'), invoke_without_command=True)
    @has_permissions(manage_channels=True)
    async def reactionmenu_group(self, ctx):
        "command group for !reactionmenu"

    """--------------------------------------------------------------------------------------------------------------------------"""

    @reactionmenu_group.command(name='create', aliases=('add', 'c', 'a'))
    @needs_database
    async def reactionmenu_create(self, ctx, *, name: str, db=Database()):
        #
        # ✓ check if menu with <name> does not already exist
        # ✓ send message "Reactionmenu <name>"
        # ✓ insert menu into database
        # ✓ disable sending messages & reacting
        # ✓ commit and clean
        #
        self.log.info("")
        guild, channel = ctx.guild, ctx.channel

        # 1
        self.log.info("check if menu with <name> does not already exist")
        await db.execute("""
            SELECT * FROM   reactionmenu
            WHERE  channel_id = %s AND name LIKE %s AND deleted_at IS NULL
            LIMIT 1
        """, (channel.id, name))
        if await db.fetchone():
            await ctx.send("`[ERROR] Reactionmenu with this name already exists`", delete_after=5)
            await db.rollback()
            return

        # 2
        self.log.info("send message \"Reactionmenu <name>\"")
        message = await ctx.send(f"**Reactionmenu {name}**")
        await self.bot.trigger_event("on_message", message)

        # 3
        self.log.info("insert menu into database")
        await db.execute("""
            INSERT INTO reactionmenu (channel_id, message_id, name)
                   VALUES (%s, %s, %s)""", (channel.id, message.id, name))

        # 4
        self.log.info("disable sending messages & reacting")
        perms = {
            guild.default_role: discord.PermissionOverwrite(
                add_reactions=False, send_messages=False),
            self.bot.user: discord.PermissionOverwrite(
                add_reactions=True, send_messages=True)
        }
        for target, overwrite in perms.items():
            await channel.set_permissions(target, overwrite=overwrite)

        # 5
        self.log.info("commit and clean")
        await db.commit()
        try:
            await ctx.message.delete()
        except:
            pass

        self.log.info("")

    @reactionmenu_group.command(name='delete', aliases=('remove', 'del', 'rm'))
    @needs_database
    async def reactionmenu_delete(self, ctx, *, name: str, db=Database()):
        #
        # ✓ fetch menu to delete
        # ✓ get section(s) which are to be deleted
        # ✓ call section(s)_delete
        # ✓ delete message "Reactionmenu <name>"
        # ✓ mark menu as deleted
        # ✓ commit and clean
        #
        self.log.info("")
        guild, channel = ctx.guild, ctx.channel

        # 1
        self.log.info("fetch menu to delete")
        await db.execute("""
            SELECT * FROM reactionmenu
            WHERE channel_id = %s AND name LIKE %s AND deleted_at IS NULL
        """, (channel.id, name))
        row = await db.fetchone()

        if not row:
            await ctx.send("`[ERROR] Reactionmenu not found`", delete_after=5)
            await db.rollback()
            return

        # 2
        self.log.info("get section(s) which are to be deleted")
        await db.execute("""
            SELECT * FROM   reactionmenu_section
            WHERE  reactionmenu_id = %s AND deleted_at IS NULL""", (row["id"],))
        rows = await db.fetchall()

        # 3
        self.log.info("call section(s)_delete")
        for section in rows:
            await self.section_delete.callback(self, ctx, name=section["text"], from_reactionmenu=name)

        # 4
        self.log.info("delete message \"Reactionmenu <name>\"")
        try:
            message = await channel.fetch_message(row["message_id"])
            await message.delete()
        except:
            pass

        # 5
        self.log.info("mark menu as deleted")
        await db.execute("""
            UPDATE reactionmenu
            SET deleted_at = NOW()
            WHERE channel_id = %s AND name LIKE %s AND deleted_at IS NULL
        """, (channel.id, name))

        # 6
        self.log.info("commit and clean")
        await db.commit()
        try:
            await ctx.message.delete()
        except:
            pass

        self.log.info("")

    """--------------------------------------------------------------------------------------------------------------------------"""

    @reactionmenu_group.group(name='section', aliases=('sec',), invoke_without_command=True)
    @needs_database
    async def reactionmenu_section_group(self, ctx, db=Database()):
        "command group for !reactionmenu section"

    """--------------------------------------------------------------------------------------------------------------------------"""

    @reactionmenu_section_group.command(name='create', aliases=('add', 'c', 'a'))
    @needs_database
    async def section_create(self, ctx, name: str, *, args: str = None, to_reactionmenu: str = None, db=Database()):
        #
        # ✓ parse input
        # ✓ validate input
        # ✓ if not to_reactionmenu provided, get first or error on multiple
        # ✓ get image with text {name} and send it
        # ✓ create category, set permissions
        # ✓ insert section into database
        # ✓ select inserted section (get id)
        # ✓ send 5 messages for options
        # ✓ insert those 5 messages into database
        # ✓ commit and clean
        #
        self.log.info("")
        guild, channel = ctx.guild, ctx.channel

        # 1
        self.log.info("parse input")
        args = self._parse_arguments(args)
        to_reactionmenu = args.get("to_reactionmenu", to_reactionmenu)

        # 2
        self.log.info("validate input")
        name = name.upper()
        if len(name) > 11:
            await ctx.send("`[ERROR] section name can be up to 11 letters long`", delete_after=5)
            return

        # 3
        self.log.info("if not to_reactionmenu provided, get first or error on multiple")
        reactionmenu = await self.get_reactionmenu(ctx, to_reactionmenu, db=db)
        if not reactionmenu:
            return

        # 4
        self.log.info("get image with text {name} and send it")
        filename = f"assets/{reactionmenu['name']}-{name}.png"
        image = self.generate_section_image(name)
        image.save(filename)
        message = await ctx.send(file=File(filename, filename=f"{image}.png"))
        os.remove(filename)

        # 5
        self.log.info("create category, set permissions")
        perms = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            self.bot.user: discord.PermissionOverwrite(read_messages=True)
        }
        category = await guild.create_category(name, overwrites=perms)
        await self.bot.trigger_event("on_guild_channel_create", category)

        # 6
        self.log.info("insert section into database")
        await db.execute("""
            INSERT INTO reactionmenu_section
                (reactionmenu_id, message_id, `text`, rep_category_id)
            VALUES (%s, %s, %s, %s)
        """, (reactionmenu["id"], message.id, name, category.id))
        await db.commit()

        # 7
        self.log.info("select inserted section (get id)")
        await db.execute("""
            SELECT * FROM reactionmenu_section
            WHERE reactionmenu_id = %s AND message_id = %s AND deleted_at IS NULL
        """, (reactionmenu["id"], message.id))
        reactionmenu_section = await db.fetchone()

        # 8
        self.log.info("send 5 messages for options")
        messages = []
        for i in range(5):
            messages.append(await ctx.send("_ _"))

        # 9
        self.log.info("insert those 5 messages into database")
        await db.executemany("""
            INSERT INTO reactionmenu_section_option
                (section_id, message_id)
            VALUES (%s, %s)
        """, [(reactionmenu_section["id"], msg.id) for msg in messages])

        # 10
        self.log.info("commit and clean")
        await db.commit()
        try:
            await ctx.message.delete()
        except:
            pass

        self.log.info("")

    """--------------------------------------------------------------------------------------------------------------------------"""

    @reactionmenu_section_group.command(name='delete', aliases=('remove', 'del', 'rm'))
    @needs_database
    async def section_delete(self, ctx, name: str, *, args: str = None, from_reactionmenu: str = None, db=Database()):
        #
        # ✓ parse input
        # ✓ validate input
        # ✓ if not to_reactionmenu provided, get first or error on multiple
        # ✓ fetch section to delete
        # ✓ get option(s) which are to be deleted
        # ✓ call option(s)_delete
        # ✓ delete image with text {name}
        # ✓ mark section as deleted
        # ✓ delete empty messages
        # ✓ delete category channel
        # ✓ commit and clean
        #
        self.log.info("")
        guild, channel = ctx.guild, ctx.channel

        # 1
        self.log.info("parse input")
        args = self._parse_arguments(args)
        from_reactionmenu = args.get("from_reactionmenu", from_reactionmenu)

        # 2
        self.log.info("validate input")
        name = name.upper()

        # 3
        self.log.info("if not to_reactionmenu provided, get first or error on multiple")
        reactionmenu = await self.get_reactionmenu(ctx, from_reactionmenu, db=db)
        if not reactionmenu:
            return

        # 4
        self.log.info("fetch section to delete")
        await db.execute("""
            SELECT * FROM reactionmenu_section
            WHERE reactionmenu_id = %s AND `text` LIKE %s AND deleted_at IS NULL
        """, (reactionmenu["id"], name))
        section = await db.fetchone()

        if not section:
            await ctx.send("`[ERROR] Section not found`")
            return

        # 5
        self.log.info("get option(s) which are to be deleted")
        await db.execute("""
            SELECT * FROM reactionmenu_section_option AS sec_opt
            INNER JOIN reactionmenu_option AS opt
            USING (message_id)
            WHERE section_id = %s AND opt.deleted_at IS NULL
        """, (section["id"],))
        rows = await db.fetchall()

        # 6
        self.log.info("call option(s)_delete")
        for option in rows:
            await self.option_delete.callback(self, ctx, text=option["text"], from_section=name, from_reactionmenu=reactionmenu["name"])

        # 7
        self.log.info("delete image with text {name}")
        try:
            message = await channel.fetch_message(section["message_id"])
            await message.delete()
        except:
            pass

        # 8
        self.log.info("mark section as deleted")
        await db.execute("""
            UPDATE reactionmenu_section
            SET deleted_at = NOW()
            WHERE reactionmenu_id = %s AND `text` LIKE %s AND deleted_at IS NULL
        """, (reactionmenu["id"], name))

        # 9
        self.log.info("delete empty messages")
        await db.execute("""
            SELECT * FROM reactionmenu_section_option
            WHERE options = 0 AND section_id = %s AND deleted_at IS NULL
        """, (section["id"],))
        rows = await db.fetchall()
        print(len(rows), rows)

        for row in rows:
            msg = await channel.fetch_message(row["message_id"])
            await msg.delete()

        await db.execute("""
            UPDATE reactionmenu_section_option
            SET deleted_at = NOW()
            WHERE options = 0 AND section_id = %s
        """, (section["id"],))

        # 10
        self.log.info("delete category channel")
        category = core.utils.get(guild.categories, id=section["rep_category_id"])
        if category:
            await category.delete()

        # 11
        self.log.info("commit and clean")
        await db.commit()
        try:
            await ctx.message.delete()
        except:
            pass

        self.log.info("")

    async def get_reactionmenu(self, ctx, to_reactionmenu: str = None, db=Database()):
        guild, channel = ctx.guild, ctx.channel

        if not to_reactionmenu:
            await db.execute("""
                SELECT * FROM reactionmenu
                WHERE channel_id = %s AND deleted_at IS NULL
            """, (channel.id,))
            reactionmenu = await db.fetchall()

            if len(reactionmenu) > 1:
                await ctx.send("`[ERROR] Multiple reactionmenus found, please use to_reactionmenu/from_reactionmenu=<name> to specify which one to use`", delete_after=5)
                return

        else:
            await db.execute("""
                SELECT * FROM reactionmenu
                WHERE name LIKE %s AND deleted_at IS NULL
            """, (to_reactionmenu,))
            reactionmenu = await db.fetchall()

        if not reactionmenu:
            await ctx.send("`[ERROR] Reactionmenu not found`", delete_after=5)
            return

        reactionmenu = reactionmenu[0]

        return reactionmenu

    """--------------------------------------------------------------------------------------------------------------------------"""

    @reactionmenu_group.group(name='option', aliases=('opt', 'o'), invoke_without_command=True)
    @needs_database
    async def reactionmenu_option_group(self, ctx, db=Database()):
        pass

    """--------------------------------------------------------------------------------------------------------------------------"""

    @reactionmenu_option_group.command(name='create', aliases=('add', 'c', 'a'))
    @needs_database
    async def option_create(self, ctx, text: str, *, args: str = None, to_section: str = None, to_reactionmenu: str = None, db=Database()):
        #
        # ✓ parse input
        # ✓ if not to_reactionmenu provided, get first or error on multiple
        # ✓ if not to_section provided, get first or error on multiple
        # ✓ select the first non-full message
        # ✓ limit the options count to 40
        # ✓ append <emoji> <text> to the message
        # ✓ create text_channel, inherit permissions
        # ✓ insert option into database
        # ✓ commit and clean
        #
        self.log.info("")
        guild, channel = ctx.guild, ctx.channel

        # 1
        self.log.info("parse input")
        args = self._parse_arguments(args)
        to_reactionmenu = args.get("to_reactionmenu", to_reactionmenu)

        # 2
        self.log.info("if not to_reactionmenu provided, get first or error on multiple")
        reactionmenu = await self.get_reactionmenu(ctx, to_reactionmenu, db=db)
        if not reactionmenu:
            return

        # 3
        self.log.info("if not to_section provided, get first or error on multiple")
        section = await self.get_section(ctx, reactionmenu, to_section, db=db)
        if not section:
            return

        # 4
        self.log.info("select the first non-full message")
        await db.execute("""
            SELECT * FROM reactionmenu_section_option
            WHERE section_id = %s AND NOT is_full
            ORDER BY order_id ASC
        """, (section["id"],))
        messages = await db.fetchall()

        if not messages:
            await ctx.send("`[ERROR] Section is full, cannot add option`", delete_after=5)
            return

        # 5
        self.log.info("limit the options count to 40")
        if section['options'] > 40:
            await ctx.send("`[ERROR] Section can only have 40 options`")
            return

        # 6
        self.log.info("append <emoji> <text> to the message")
        msg = await channel.fetch_message(messages[0]["message_id"])
        content = msg.content if msg.content != "_ _" else ""
        new_content = ""

        emoji = core.utils.get(self.bot.emojis, name=f"num{section['options']+1}")
        option_text = f"{emoji} {text}"
        if len(content) + len(option_text) < 2000 and content.count("\n") + 1 < 10:
            new_content = content + f"\n{option_text}"

        else:
            await db.execute("""
                UPDATE reactionmenu_section_option
                SET is_full=1
                WHERE section_id = %s AND message_id = %s
            """, (section["id"], messages[0]["message_id"]))

            if len(messages) <= 1:
                return

            msg = await channel.fetch_message(messages[1]["message_id"])
            new_content = option_text
            content = new_content

        await msg.edit(content=new_content)
        self.bot.loop.create_task(msg.add_reaction(emoji))

        # 7
        self.log.info("create text_channel, inherit permissions")
        category = core.utils.get(guild.categories, id=section["rep_category_id"])
        chnl = await guild.create_text_channel(text, category=category)
        await self.bot.trigger_event("on_guild_channel_create", chnl)

        # 8
        self.log.info("insert option into database")
        await db.execute("""
            INSERT INTO reactionmenu_option
                (message_id, emoji, `text`, rep_channel_id)
            VALUES (%s, %s, %s, %s)
        """, (msg.id, str(emoji), text, chnl.id))

        # 9
        self.log.info("commit and clean")
        await db.commit()
        try:
            await ctx.message.delete()
        except:
            pass

        self.log.info("")

    """--------------------------------------------------------------------------------------------------------------------------"""

    @reactionmenu_option_group.command(name='delete', aliases=('remove', 'del', 'rm'))
    @needs_database
    async def option_delete(self, ctx, text: str, *, args: str = None, from_section: str = None, from_reactionmenu: str = None, db=Database()):
        #
        # ✓ parse input
        # ✓ if not to_reactionmenu provided, get first or error on multiple
        # ✓ if not to_section provided, get first or error on multiple
        # ✓ fetch option to delete
        # ✓ remove {emoji} {text} from message
        # ✓ remove reactions for {emoji}
        # ✓ mark option as deleted
        # ✓ delete text_channel
        # ✓ commit and clean
        #
        self.log.info("")
        guild, channel = ctx.guild, ctx.channel

        # 1
        self.log.info("parse input")
        args = self._parse_arguments(args)
        from_reactionmenu = args.get("from_reactionmenu", from_reactionmenu)
        from_section = args.get("from_section", from_section)

        # 2
        self.log.info("if not to_reactionmenu provided, get first or error on multiple")
        reactionmenu = await self.get_reactionmenu(ctx, from_reactionmenu, db=db)
        if not reactionmenu:
            return

        # 3
        self.log.info("if not to_section provided, get first or error on multiple")
        section = await self.get_section(ctx, reactionmenu, from_section, db=db)
        if not section:
            return

        # 4
        self.log.info("fetch option to delete")
        await db.execute("""
            SELECT * FROM reactionmenu_option AS opt
            INNER JOIN reactionmenu_section_option AS sec_opt
            USING (message_id)
            WHERE section_id = %s AND `text` LIKE %s AND opt.deleted_at IS NULL
        """, (section["id"], text))
        row = await db.fetchone()

        if not row:
            await ctx.send("`[ERROR] Option not found`")
            return

        # 5
        self.log.info("remove {emoji} {text} from message")
        msg = await channel.fetch_message(row["message_id"])
        content = msg.content if msg.content != "_ _" else ""
        new_content = ""

        found = re.search(r"\:([^:]+)\:", row["emoji"])
        if not found:
            await ctx.send("`[ERROR] Emoji not found`")
            return
        emoji_name = found.group(1)
        emoji = core.utils.get(self.bot.emojis, name=emoji_name)

        option_text = f"{emoji} {text}"
        found = re.search(rf"({option_text}\n?)", content)
        if not found:
            await ctx.send("`[ERROR] Option not found in message`")
            return

        _from, _to = found.span()
        new_content = (content[:_from] + content[_to:]).strip()
        new_content = new_content if new_content != "" else "_ _"
        await msg.edit(content=new_content)

        # 6
        self.log.info("remove reactions for {emoji}")
        reaction = core.utils.get(msg.reactions, emoji=emoji)
        async for user in reaction.users():
            await msg.remove_reaction(emoji, user)

        # 7
        self.log.info("mark option as deleted")
        await db.execute("""
            UPDATE reactionmenu_option
            SET deleted_at = NOW()
            WHERE message_id = %s AND `text` LIKE %s AND deleted_at IS NULL
        """, (row["message_id"], text))

        # 8
        self.log.info("delete text_channel")
        chnl = core.utils.get(channel.guild.channels, id=row["rep_channel_id"])
        if chnl:
            if chnl.last_message_id:
                await ctx.send("`[WARNING] channel still has messages, skipping delete`")
            else:
                await chnl.delete()

        # 9
        self.log.info("commit and clean")
        await db.commit()
        try:
            await ctx.message.delete()
        except:
            pass

        self.log.info("")

    async def get_section(self, ctx, reactionmenu, to_section: str = None, db=Database()):
        guild, channel = ctx.guild, ctx.channel

        if not to_section:
            await db.execute("""
                SELECT * FROM reactionmenu_section
                WHERE reactionmenu_id = %s AND deleted_at IS NULL
            """, (reactionmenu["id"],))
            section = await db.fetchall()

            if len(section) > 1:
                await ctx.send("`[ERROR] Multiple sections found, please use to_section/from_section=<name> to specify which one to use`", delete_after=5)
                return

        else:
            await db.execute("""
                SELECT * FROM reactionmenu_section
                WHERE `text` LIKE %s AND deleted_at IS NULL
            """, (to_section,))
            section = await db.fetchall()

        if not section:
            await ctx.send("`[ERROR] Section not found`", delete_after=5)
            return
        section = section[0]

        return section

    """--------------------------------------------------------------------------------------------------------------------------"""

    @reactionmenu_group.command(name="setup")
    @needs_database
    async def setup(self, ctx, filepath: str, reactionmenu_name: str, db=Database()):
        #
        # call reactionmenu_create
        # for section
        #    call section_create
        #    for option
        #        call option_create
        #
        pass

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_raw_reaction_add(self, payload, db=Database()):
        pass

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_raw_reaction_remove(self, payload, db=Database()):
        pass

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_ready(self, db=Database()):
        pass

    """--------------------------------------------------------------------------------------------------------------------------"""

    @staticmethod
    def generate_section_image(text):
        ##
        # GENERATE image in format
        ##
        # -------------
        # TEXT HERE
        # -------------
        ##

        W, H = (799, 186)

        bg = (255, 255, 255)
        fg = (0, 0, 0)

        im = Image.new('RGBA', (W, H), bg + (255,))
        fnt = ImageFont.truetype('assets/muni-regular.ttf', 96)

        draw = ImageDraw.Draw(im)

        draw.line((20, 20, im.size[0] - 20, 20), fill=fg, width=5)
        draw.line((20, im.size[1] - 20, im.size[0] - 20, im.size[1] - 20), fill=fg, width=5)

        w, h = draw.textsize(text.upper(), font=fnt)
        draw.text(((W - w) / 2, (H - h) / 2 - 10), text.upper(), font=fnt, fill=fg)

        return im

    @staticmethod
    def _parse_arguments(text):
        args = {}

        if not isinstance(text, str):
            return args

        found = re.search(r"(\w+)\s*\=\s*(\w+)", text)
        while found:
            args[found.group(1)] = found.group(2)

            _from, _to = found.span()
            text = (text[:_from] + text[_to:]).strip()
            found = re.search(r"(\w+)\s*\=\s*(\w+)", text)

        return args


def setup(bot):
    bot.add_cog(ReactionPicker(bot))
