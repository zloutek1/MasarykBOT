import os
import logging
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime, timedelta
from typing import Union

from discord import File, PermissionOverwrite, Embed, Color, TextChannel, User
from discord.ext import commands
from discord.ext.commands import has_permissions

import core.utils.get
from core.utils.db import Database
from core.utils.checks import needs_database, safe

from dotenv import load_dotenv
load_dotenv()


class Reactionmenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger(__name__)

        self.channel_cache = {}
        self.in_channels = set()
        self.updating_channels = {}

        self.NEED_REACTIONS = int(os.getenv("NEED_REACTIONS"))

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.group(name='reactionmenu', aliases=('rolemenu', 'rlm'))
    @has_permissions(manage_channels=True)
    async def reactionmenu_group(self, ctx):
        "command group for !reactionmenu"

    @reactionmenu_group.command(name="create", aliases=("add",))
    @needs_database
    async def reactionmenu_create(self, ctx, *, name: str, db: Database = None):
        """
        generate image in format
            -----------
              N A M E
            -----------
        send the image to channel

        disable permissions for Student to send messages
        add cooldown of 5 seconds

        send additional 5 empty (_ _) messages

        save all the data into the database
        """

        guild = ctx.guild
        channel = ctx.channel
        self.updating_channels[channel.id] = True

        self.log.info(f"creating reactionmenu {name}")
        # set permissions to current channel
        self.log.info("setting permission to current channel")
        perms = {
            ctx.get_role("Student"): PermissionOverwrite(
                add_reactions=False, send_messages=False),
            self.bot.user: PermissionOverwrite(
                add_reactions=True, send_messages=True)
        }
        for target, overwrite in perms.items():
            await channel.set_permissions(target, overwrite=overwrite)

        # create category and set permissions
        self.log.info("createing category with permissions")
        perms = {
            ctx.get_role("Student"): PermissionOverwrite(
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
            INSERT INTO reactionmenu_sections (
                channel_id, message_id, rep_category_id, name)
            VALUES (%s, %s, %s, %s)
        """, (channel.id, message.id, category.id, name))
        await db.commit()

        self.log.info("inserting five empty messages into database")
        await db.executemany("""
            INSERT INTO reactionmenu_messages (
                reactionmenu_message_id, message_id)
            VALUES (%s, %s)
        """, opt_messages)
        await db.commit()

        # clean
        self.log.info("finishing reactionmenu creation")
        await db.commit()
        await safe(ctx.message.delete)()

        self.updating_channels[channel.id] = False
        return message.id

    @reactionmenu_group.group(name="option", aliases=("opt",))
    async def option_group(self, ctx):
        "command group for !reactionmenu option"

    @option_group.command(name="create", aliases=("add",))
    @needs_database
    async def option_create(self, ctx, to_menu: int=None, *, text: str, db: Database = None):
        """
        fetch the message in the correct section
        append the {text} in the message if it fists
        set the {text} in the next message otherwise

        update all the values in the database
        """
        channel = ctx.channel
        self.updating_channels[channel.id] = True

        await db.commit()
        self.log.info(f"creating option {text}")

        async def select_reactionmenu_from_db(to_menu):
            self.log.info("selecting reactionmenu from database")
            await db.execute("""
                SELECT * FROM reactionmenu_sections
                WHERE message_id = %s
            """, (to_menu,))
            reactionmenu = await db.fetchone()

            if not reactionmenu:
                await safe(ctx.message.delete(delay=5))
                await ctx.send("Unknown reactionmenu, argument to_menu must be id of the message", delete_after=5)
                return False

            return reactionmenu

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

        async def get_option_count(reactionmenu):
            self.log.info("getting No. of options in reactionmenu")
            await db.execute("""
                SELECT COUNT(*) AS `count` FROM reactionmenu_options
                INNER JOIN reactionmenu_messages USING (message_id)
                WHERE reactionmenu_message_id = %s
            """, (reactionmenu["message_id"],))
            options = (await db.fetchone())["count"]

            return options

        async def get_DC_message(reactionmenu_message):
            self.log.info("getting Discord's message object")
            option_message = await channel.fetch_message(reactionmenu_message["message_id"])

            if not option_message:
                await safe(ctx.message.delete(delay=5))
                await ctx.send("It appears that the message does not exist", delete_after=5)
                return False
            return option_message

        async def insert_option_into_db(option_message, emoji):
            self.log.info("inserting option into databse")
            await db.execute("""
                INSERT INTO reactionmenu_options
                    (message_id, rep_channel_id, emoji, `text`)
                VALUES (%s, %s, %s, %s)
            """, (option_message.id, None, str(emoji), text))
            await db.commit()

        async def modify_content(option_message, options):
            self.log.info("preparing the new content of the message")
            content = option_message.content
            emoji = ctx.get_emoji(name=f"num{options+1}")
            option_text = f"{emoji}   {text}"

            if len(content) + len(option_text) < 2000 and content.count("\n") < 10:
                self.log.info("editing to new content")
                await option_message.edit(content=content + f"\n{option_text}")
                # await option_message.add_reaction(emoji)

                await insert_option_into_db(option_message, emoji)
                return True

            self.log.info("marking the message as full, retrying...")
            await db.execute("""
                UPDATE reactionmenu_messages
                SET is_full = true
                WHERE message_id = %s
            """, (option_message.id))
            await db.commit()

        """
        call all functions
        defined above
        """

        reactionmenu = await select_reactionmenu_from_db(to_menu)
        if not reactionmenu:
            return False

        while True:
            reactionmenu_message = await select_message_from_db(reactionmenu)
            options = await get_option_count(reactionmenu)

            option_message = await get_DC_message(reactionmenu_message)
            if not option_message:
                self.updating_channels[channel.id] = False
                return False

            if await modify_content(option_message, options):
                break

        # clean
        self.log.info("finishing option addition")
        await db.commit()
        await safe(ctx.message.delete)()

        self.updating_channels[channel.id] = False
        return option_message.id

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

        bg = (54, 57, 63, 0)
        fg = (173, 216, 230)

        im = Image.new('RGBA', (W, H), bg)
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

    @reactionmenu_group.command(name="recover_database")
    @needs_database
    @has_permissions(administrator=True)
    async def recover_database(self, ctx, channel: TextChannel, *, db: Database = None):
        """
        recover the database from a channel
        if the message has attachemtns - it is a section
            determine the section name based on filename
            save the message into the database
        if the message is plain - it is an option
            add the option into the database
        """
        await ctx.message.delete()
        menu_id = None

        async for message in channel.history(limit=1_000_000, oldest_first=True):
            if message.embeds:
                continue

            if message.attachments:
                text = message.attachments[0].filename.split(
                    "-", 1)[1].rstrip(".png")
                rep_category = ctx.get_category(text)
                if rep_category is None:
                    rep_category = ctx.get_category(text + "+")

                await db.execute("""
                    INSERT INTO reactionmenu_sections
                        (channel_id, message_id, rep_category_id, name)
                    VALUES (%s, %s, %s, %s)
                """, (channel.id, message.id, rep_category.id, text))
                await db.commit()

                menu_id = message.id
                self.log.info(f"recovered reactionmenu section {text}")
                continue

            await db.execute("""
                INSERT INTO reactionmenu_messages
                    (reactionmenu_message_id, message_id)
                VALUES (%s, %s)
            """, (menu_id, message.id))
            await db.commit()

            content = message.content.replace("_ _", "").strip()
            if content:
                for line in content.split("\n"):
                    emoji, text = line.split(" ", 1)
                    rep_channel = ctx.get_channel(
                        "-".join(text.lower().split()))

                    await db.execute("""
                        INSERT INTO reactionmenu_options
                            (message_id, rep_channel_id, emoji, `text`)
                        VALUES (%s, %s, %s, %s)
                    """, (message.id, rep_channel.id if rep_channel else None, emoji, text))
                    await db.commit()
                    self.log.info(f"recovered reactionmenu option {text}")

    """---------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def subject_update(self, ctx, text, event_type, *, db: Database = None):
        """
        find queries {text} in database
        if the subject is not found - print error
        get the number of people signed to the subject

        if the count is enough
            dont do anything, inform author that he is in queue

        if the count is enough
            add subject to queued members
            or remove subject from the author

        update all the values in the database as well
        """
        self.updating_channels[ctx.channel.id] = True
        self.log.info(f"{event_type}: {text} for {ctx.author}")
        await safe(ctx.message.delete)()

        if ctx.channel.id not in self.in_channels:
            return

        # get reactionmenu database data
        await db.execute("""
            SELECT channel_id, rep_category_id, opts.* FROM (
                SELECT * FROM reactionmenu_options
                WHERE `text` LIKE %s AND deleted_at IS NULL
                LIMIT 1) AS opts
            INNER JOIN reactionmenu_messages AS msgs USING (message_id)
            INNER JOIN reactionmenu_sections AS secs ON (secs.message_id = msgs.reactionmenu_message_id)
            INNER JOIN reactionmenu AS menu ON (menu.section_channel_id = secs.channel_id)
            WHERE menu.message_channel_id = %s
        """, (text + "%", ctx.channel.id))
        row = await db.fetchone()
        if not row:
            await ctx.send(f"subject {text} not found", delete_after=5)
            return

        text = row["text"]
        subject_code = row["text"].split(" ", 1)[0]

        self.log.info(f"updating subject with code {subject_code}")

        # get  user count for subject
        async def get_count():
            await db.execute("""
                SELECT COUNT(*) AS `count` FROM reactionmenu_users
                WHERE channel_id = %s AND `text` LIKE %s
            """, (ctx.channel.id, text))
            count = (await db.fetchone())["count"]
            return count

        async def get_rep_channel(row, also_create=True):
            """
            get the rep_channel
            get the channel by id
            or get the channel by name
            or create the channel if also_create is turned on

            insert the channel into the database
            """
            rep_channel = self.channel_cache.get(row["rep_channel_id"])
            if rep_channel is None:
                rep_channel = ctx.get_channel(
                    id=row["rep_channel_id"])

            if rep_channel is None:
                rep_channel = ctx.get_channel(ctx.channel_name(text))
                if rep_channel:
                    row["rep_channel_id"] = rep_channel.id

            if rep_channel is None and also_create:
                rep_channel = await ctx.guild.create_text_channel(
                    name=row["text"],
                    position=int(row["emoji"].split(":")[1].lstrip("num")) - 1,
                    category=self.bot.get_channel(row["rep_category_id"])
                )
                row["rep_channel_id"] = rep_channel.id

            self.channel_cache[row["rep_channel_id"]] = rep_channel

            if rep_channel:
                await db.execute("""
                    UPDATE reactionmenu_options
                    SET rep_channel_id = %s
                    WHERE message_id = %s AND emoji = %s
                """, (rep_channel.id, row["message_id"], row["emoji"]))
                await db.commit()

            return rep_channel

        count = await get_count()
        self.log.info(f"users count {count}")

        if event_type == "REACTION_ADD":
            if count < self.NEED_REACTIONS:
                self.log.info(f"need more reactions")
                # needs more users
                need_more = (self.NEED_REACTIONS) - count
                embed = Embed(
                    description=f"Díky za zájem o {subject_code} {ctx.author.mention}. Uživatel přidán na čekací listinu, čekáte ještě na {need_more} studenty.", color=Color.green())
                await ctx.channel.send(embed=embed, delete_after=5)

            else:
                self.log.info(f"got enough reactions")
                # adding user
                embed = Embed(
                    description=f"Předmět {subject_code} úspěšně zapsán studentem {ctx.author.mention}.", color=Color.green())
                await ctx.channel.send(embed=embed, delete_after=5)

                rep_channel = await get_rep_channel(row, also_create=True)
                self.log.info(f"got rep_channel {rep_channel}")

                await db.execute("""
                    SELECT * FROM reactionmenu_users
                    WHERE channel_id = %s AND `text` LIKE %s
                """, (row["channel_id"], text))
                rows = await db.fetchall()
                users = [ctx.get_user(id=row["user_id"]) for row in rows]
                self.log.info(f"found users {list(map(str, users))}")

                for user in users + [ctx.author]:
                    await rep_channel.set_permissions(user, read_messages=True)

            await db.execute("""
                INSERT INTO reactionmenu_users
                    (channel_id, `text`, user_id)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE user_id=user_id
            """, (ctx.channel.id, text, ctx.author.id))
            await db.commit()
            self.log.info(f"inserted user {ctx.author} into database")

        elif event_type == "REACTION_REMOVE":
            if count < self.NEED_REACTIONS:
                self.log.info(f"not enough reactions on subject to remove")
                embed = Embed(
                    description=f"Uživatel {ctx.author.mention} uspěšně odstráněn z čekací listiny na předmět {subject_code}.", color=Color.green())
                await ctx.channel.send(embed=embed, delete_after=5)

            else:
                self.log.info(f"enough reactions on subject to remove")
                embed = Embed(
                    description=f"Předmět {subject_code} úspěšně odepsán studentem {ctx.author.mention}.", color=Color.green())
                await ctx.channel.send(embed=embed, delete_after=5)

                rep_channel = await get_rep_channel(row, also_create=False)
                self.log.info(
                    f"rep_channel to remove user from {rep_channel}")

                if rep_channel is not None:
                    await rep_channel.set_permissions(ctx.author, read_messages=None)
                    self.log.info(
                        f"disabling permission from {str(ctx.author)}")

            await db.execute("""
                DELETE FROM reactionmenu_users
                WHERE channel_id = %s AND `text` LIKE %s AND user_id = %s
            """, (ctx.channel.id, text, ctx.author.id))
            await db.commit()
            self.log.info(f"deleting {str(ctx.author)} from database")

        self.updating_channels[ctx.channel.id] = False

    """---------------------------------------------------------------------------------------------------------------------------"""

    @commands.group(name="subject", aliases=("predmet",))
    async def subject(self, ctx):
        pass

    @subject.command(name="show", aliases=("create", "add"))
    async def subject_add(self, ctx, *, text):
        text = text.strip("<").strip(">")
        await self.subject_update(ctx, text, event_type="REACTION_ADD")

    @subject.command(name="hide", aliases=("del", "remove"))
    async def subject_remove(self, ctx, *, text):
        text = text.strip("<").strip(">")
        await self.subject_update(ctx, text, event_type="REACTION_REMOVE")

    """---------------------------------------------------------------------------------------------------------------------------"""

    @subject.command(name="status", aliases=("stats", ))
    @needs_database
    async def subject_status(self, ctx, *, query_by: Union[User, str]=10, db: Database):
        top10 = True if query_by == 10 else False
        user = True if isinstance(query_by, User) else False
        subject = True if isinstance(query_by, str) else False

        if top10:
            query = """
                SELECT COUNT(*) AS `count`, users.* FROM reactionmenu_users AS users
                GROUP BY `text`
                ORDER BY `count` DESC
                LIMIT %s
            """
            query_by = 10
        elif user:
            query = """
                SELECT "-" AS `count`, users.* FROM reactionmenu_users AS users
                WHERE user_id = %s
            """
            query_by = query_by.id
        elif subject:
            query = """
                SELECT COUNT(*) AS `count`, users.* FROM reactionmenu_users AS users
                WHERE `text` LIKE %s
                GROUP BY `text`
                ORDER BY `count` DESC
            """
            query_by = query_by + "%"

        await db.execute(query, (query_by,))
        rows = await db.fetchall()

        txt = ""
        for row in rows:
            txt += "`{count}` {subject}\n".format(
                count=row["count"], subject=row["text"])

        if txt != "":
            await ctx.send(txt)
        else:
            await ctx.send("got empty output.")

    """---------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    @needs_database
    async def on_ready(self, *, db: Database = None):
        """
        save reactionmenu channels into variable
        for quicker access

        parse each category and channels
        sort them alphabetically
        """
        self.bot.readyCogs[self.__class__.__name__] = False

        await db.execute("SELECT * FROM reactionmenu WHERE deleted_at IS NULL")
        rows = await db.fetchall()
        for row in rows:
            section_channel = self.bot.get_channel(row["section_channel_id"])
            message_channel = self.bot.get_channel(row["message_channel_id"])

            if message_channel is not None:
                self.in_channels.add(message_channel.id)

        await db.execute("""
            SELECT channel_id, rep_category_id, opts.* FROM (
                SELECT * FROM reactionmenu_options
                WHERE deleted_at IS NULL) AS opts
            INNER JOIN reactionmenu_messages AS msgs USING (message_id)
            INNER JOIN reactionmenu_sections AS secs ON (secs.message_id = msgs.reactionmenu_message_id)
            ORDER BY `text` DESC
        """)
        rows = await db.fetchall()

        self.log.info("Starting reordering channels")
        categories = {}
        for row in rows:
            category_id = row["rep_category_id"]
            if categories.get(category_id) is None:
                categories[category_id] = self.bot.get_channel(category_id)
            category = categories.get(category_id)

            # skip if already sorted
            if not category:
                continue

            channels = list(map(str, category.channels))
            if channels == sorted(channels):
                continue

            channel = self.bot.get_channel(row["rep_channel_id"])
            if channel:
                await channel.edit(
                    name=row["text"],
                    position=0,
                    category=category
                )
                self.log.info(f"reordered channel {channel}")

        self.log.info("Finished reordering channels")
        self.bot.readyCogs[self.__class__.__name__] = True

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        delete each message in the channel if
        channel is not updating
        """
        if message.channel.id not in self.in_channels:
            return
        if self.updating_channels.get(message.channel.id, False):
            return
        await safe(message.delete)(delay=0.2)

    @commands.command()
    @has_permissions(administrator=True)
    async def resend_subject_message(self, ctx):
        menu_text_channel = ctx.get_channel("výběr-předmětů")
        if not menu_text_channel:
            return

        self.updating_channels[menu_text_channel.id] = True
        embed = Embed(
            description="""
                :warning: předmět si múžeš zapsat/zrušit každých 5 sekund
                příkazem `!subject add/remove <subject_code>`

                :point_down: Zapiš si své předměty zde :point_down:""".strip(),
            color=Color(0xFFD800))
        await menu_text_channel.send(embed=embed)
        self.updating_channels[menu_text_channel.id] = False


def setup(bot):
    bot.add_cog(Reactionmenu(bot))
