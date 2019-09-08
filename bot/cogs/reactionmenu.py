import os
import logging
from PIL import Image, ImageFont, ImageDraw

from discord import File, PermissionOverwrite, TextChannel
from discord.ext import commands
from discord.ext.commands import has_permissions

from core.utils.db import Database
from core.utils.checks import needs_database, safe


class Reactionmenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger(__name__)

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.group(name='reactionmenu', aliases=('rolemenu', 'rlm'))
    @has_permissions(manage_channels=True)
    async def reactionmenu_group(self, ctx):
        "command group for !reactionmenu"

    @reactionmenu_group.command(name="create", aliases=("add",))
    @needs_database
    async def reactionmenu_create(self, ctx, *, name: str, db=Database()):
        guild = ctx.guild
        channel = ctx.channel

        # set permissions to current channel
        self.log.info("setting permission to current channel")
        perms = {
            guild.default_role: PermissionOverwrite(
                add_reactions=False, send_messages=False),
            self.bot.user: PermissionOverwrite(
                add_reactions=True, send_messages=True)
        }
        for target, overwrite in perms.items():
            await channel.set_permissions(target, overwrite=overwrite)

        # create category and set permissions
        self.log.info("createing category with permissions")
        perms = {
            guild.default_role: PermissionOverwrite(
                read_messages=False),
            self.bot.user: PermissionOverwrite(
                read_messages=True)
        }
        category = await guild.create_category(name, overwrites=perms)
        await self.bot.trigger_event("on_guild_channel_create", category)

        # send image
        self.log.info("sending image to channel")
        filename = f"assets/{channel.id}-{name}.png"
        image = self.generate_section_image(name)
        image.save(filename)
        message = await ctx.send(file=File(filename, filename=filename))
        os.remove(filename)

        # send 5 messages
        self.log.info("sending 5 empty messages")
        opt_messages = []
        for i in range(5):
            msg = await ctx.send("_ _")
            opt_messages.append((message.id, msg.id))

        # insert into database
        self.log.info("inserting reactionmenu into database")
        await db.execute("""
            INSERT INTO reactionmenu (
                channel_id, message_id, rep_category_id, name)
            VALUES (%s, %s, %s, %s)
        """, (channel.id, message.id, category.id, name))

        self.log.info("inserting five empty messages into database")
        await db.executemany("""
            INSERT INTO reactionmenu_messages (
                reactionmenu_message_id, message_id)
            VALUES (%s, %s)
        """, opt_messages)

        # clean
        self.log.info("finishing reactionmenu creation")
        await db.commit()
        await safe(ctx.message.delete)()

        return message.id

    @reactionmenu_group.group(name="option", aliases=("opt",))
    async def option_group(self, ctx):
        "command group for !reactionmenu option"

    @option_group.command(name="create", aliases=("add",))
    @needs_database
    async def option_create(self, ctx, to_menu: int=None, *, text: str, db=Database()):
        guild = ctx.guild
        channel = ctx.channel

        async def select_reactionmenu_from_db(to_menu):
            self.log.info("selecting reactionmenu from database")
            await db.execute("""
                SELECT * FROM reactionmenu
                WHERE message_id = %s
            """, (to_menu,))
            reactionmenu = await db.fetchone()

            if not reactionmenu:
                await safe(ctx.message.delete(delay=5))
                await ctx.send("Unknown reactionmenu, argument to_menu must be id of the message", delete_after=5)
                return False

            return reactionmenu

        async def get_option_count(reactionmenu):
            self.log.info("getting No. of options in reactionmenu")
            await db.execute("""
                SELECT COUNT(*) AS `count` FROM reactionmenu_options
                INNER JOIN reactionmenu_messages USING (message_id)
                WHERE reactionmenu_message_id = %s
            """, (reactionmenu["message_id"],))
            options = (await db.fetchone())["count"]
            return options

        async def select_message_from_db(reactionmenu):
            self.log.info("selecting messages from database")
            await db.execute("""
                SELECT * FROM reactionmenu_messages
                WHERE reactionmenu_message_id = %s AND NOT is_full
            """, (reactionmenu["message_id"],))
            reactionmenu_message = await db.fetchone()

            if not reactionmenu_message:
                await safe(ctx.message.delete(delay=5))
                await ctx.send("All messages in the reactionmenu are full", delete_after=5)
                return False

            return reactionmenu_message

        async def get_DC_message(reactionmenu_message):
            self.log.info("getting Discord's message object")
            option_message = await channel.fetch_message(reactionmenu_message["message_id"])
            if not option_message:
                await safe(ctx.message.delete(delay=5))
                await ctx.send("It appears that the message does not exist", delete_after=5)
                return False
            return option_message

        async def modify_content(option_message, options):
            nonlocal emoji

            self.log.info("preparing the new content of the message")
            content = option_message.content
            emoji = ctx.get_emoji(name=f"num{options+1}")
            option_text = f"{emoji}   {text}"

            if len(content) + len(option_text) < 2000 and content.count("\n") < 10:
                print("    adding")
                self.log.info("editing to new content")
                await option_message.edit(content=content + f"\n{option_text}")
                await option_message.add_reaction(emoji)
                return True

            self.log.info("marking the message as full, retrying...")
            await db.execute("""
                UPDATE reactionmenu_messages
                SET is_full = true
                WHERE message_id = %s
            """, (option_message.id))
            await db.commit()
            print("    extending")

        emoji = None
        reactionmenu = await select_reactionmenu_from_db(to_menu)
        while True:
            options = await get_option_count(reactionmenu)
            print(options)
            reactionmenu_message = await select_message_from_db(reactionmenu)
            option_message = await get_DC_message(reactionmenu_message)
            if await modify_content(option_message, options):
                break

        # create channel
        # category = ctx.get_category(id=reactionmenu["rep_category_id"])
        # chnl = await guild.create_text_channel(text, category=category)
        # await self.bot.trigger_event("on_guild_channel_create", chnl)

        # insert option into database
        self.log.info("inserting option into databse")
        await db.execute("""
            INSERT INTO reactionmenu_options
                (message_id, rep_channel_id, emoji, `text`)
            VALUES (%s, %s, %s, %s)
        """, (option_message.id, None, str(emoji), text))
        await db.commit()

        # clean
        self.log.info("finishing option addition")
        await db.commit()
        await safe(ctx.message.delete)()

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
        draw.line((20, im.size[1] - 20, im.size[0] - 20,
                   im.size[1] - 20), fill=fg, width=5)

        w, h = draw.textsize(text.upper(), font=fnt)
        draw.text(((W - w) / 2, (H - h) / 2 - 10),
                  text.upper(), font=fnt, fill=fg)

        return im

    """---------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def on_raw_reaction_update(self, payload, event_type: str, db=Database()):
        # is it bot?
        if payload.user_id == self.bot.user.id:
            return

        # reacted in reactionmenu channel?
        await db.execute("""
            SELECT * FROM reactionmenu
            WHERE channel_id = %s AND deleted_at IS NULL
            LIMIT 1
        """, (payload.channel_id,))
        if not await db.fetchone():
            return

        # does the option exist? get it
        await db.execute("""
            SELECT * FROM (
                SELECT * FROM reactionmenu_options
                WHERE message_id = %s AND emoji = %s AND deleted_at IS NULL
                LIMIT 1) AS sel
            INNER JOIN reactionmenu_messages AS menu_msgs
            USING (message_id)
            INNER JOIN reactionmenu
            ON (menu_msgs.reactionmenu_message_id = reactionmenu.message_id)
        """, (payload.message_id, str(payload.emoji)))
        row = await db.fetchone()
        if not row:
            return

        # get or create the channel
        guild = self.bot.get_guild(payload.guild_id)
        if row["rep_channel_id"] is None and event_type == "REACTION_ADD":
            category = guild.get_channel(row["rep_category_id"])
            position = int(payload.emoji.name.lstrip("num")) - 1
            rep_channel = await guild.create_text_channel(
                name=row["text"], category=category, position=position)

            # set the channel in the database
            await db.execute("""
                UPDATE reactionmenu_options
                SET rep_channel_id = %s
                WHERE message_id = %s AND emoji = %s
            """, (rep_channel.id, payload.message_id, str(payload.emoji)))
            await db.commit()
        else:
            rep_channel = self.bot.get_channel(row["rep_channel_id"])
        if not rep_channel:
            return

        # add permissions to the user
        author = guild.get_member(payload.user_id)
        if event_type == "REACTION_ADD":
            await rep_channel.set_permissions(author, read_messages=True)
        else:
            await rep_channel.set_permissions(author, read_messages=False)

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
    async def on_guild_channel_delete(self, channel, *, db=Database()):
        if not isinstance(channel, TextChannel):
            return

        await db.execute("""
            UPDATE reactionmenu_options
            SET rep_channel_id = NULL
            WHERE rep_channel_id = %s
        """, (channel.id,))
        await db.commit()

    """---------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_ready(self, *, db=Database()):
        self.bot.readyCogs[self.__class__.__name__] = False

        self.bot.readyCogs[self.__class__.__name__] = True


def setup(bot):
    bot.add_cog(Reactionmenu(bot))
