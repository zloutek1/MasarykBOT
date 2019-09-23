import os
import logging
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime, timedelta


from discord import File, PermissionOverwrite, Embed, Color, TextChannel
from discord.ext import commands
from discord.ext.commands import has_permissions

import core.utils.get
from core.utils.db import Database
from core.utils.checks import needs_database, safe


class Reactionmenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger(__name__)

        self.users_on_cooldown = {}
        self.channel_cache = {}

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.group(name='reactionmenu', aliases=('rolemenu', 'rlm'))
    @has_permissions(manage_channels=True)
    async def reactionmenu_group(self, ctx):
        "command group for !reactionmenu"

    @reactionmenu_group.command(name="create", aliases=("add",))
    @needs_database
    async def reactionmenu_create(self, ctx, *, name: str, db: Database = None):
        guild = ctx.guild
        channel = ctx.channel
        self.in_channels.add(channel.id)

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
            INSERT INTO reactionmenu (
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

        return message.id

    @reactionmenu_group.group(name="option", aliases=("opt",))
    async def option_group(self, ctx):
        "command group for !reactionmenu option"

    @option_group.command(name="create", aliases=("add",))
    @needs_database
    async def option_create(self, ctx, to_menu: int=None, *, text: str, db: Database = None):
        channel = ctx.channel

        await db.commit()

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
                await option_message.add_reaction(emoji)

                await insert_option_into_db(option_message, emoji)
                return True

            self.log.info("marking the message as full, retrying...")
            await db.execute("""
                UPDATE reactionmenu_messages
                SET is_full = true
                WHERE message_id = %s
            """, (option_message.id))
            await db.commit()

        reactionmenu = await select_reactionmenu_from_db(to_menu)
        if not reactionmenu:
            return False

        while True:
            reactionmenu_message = await select_message_from_db(reactionmenu)
            options = await get_option_count(reactionmenu)

            option_message = await get_DC_message(reactionmenu_message)
            if not option_message:
                return False

            if await modify_content(option_message, options):
                break

        # clean
        self.log.info("finishing option addition")
        await db.commit()
        await safe(ctx.message.delete)()

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
        menu_id = None

        async for message in channel.history(limit=1_000_000, oldest_first=True):
            if message.embeds:
                continue

            if message.attachments:
                text = message.attachments[0].filename.split(
                    "-", 1)[1].rstrip(".png")
                rep_category = ctx.get_category(text)
                if rep_category is None:
                    rep_category = ctx.get_category(text+"+")

                await db.execute("""
                    INSERT INTO reactionmenu
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

        await ctx.message.delete()

    """---------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def on_raw_reaction_update(self, payload, event_type: str, db: Database = None):
        # is it a user and in right channel?
        print("reaction")
        if (payload.user_id == self.bot.user.id or
                payload.channel_id not in self.in_channels):
            return

        cooldown = self.users_on_cooldown.get(payload.user_id)
        if cooldown and cooldown + timedelta(seconds=3) > datetime.now():
            return  # on cooldown
        print("oki pass")

        # --[]

        await db.execute("""
            SELECT channel_id, rep_category_id, opts.* FROM (
                SELECT * FROM reactionmenu_options
                WHERE message_id = %s AND emoji = %s AND deleted_at IS NULL
                LIMIT 1) AS opts
            INNER JOIN reactionmenu_messages AS msgs USING (message_id)
            INNER JOIN reactionmenu AS menu ON (menu.message_id = msgs.reactionmenu_message_id)
        """, (payload.message_id, str(payload.emoji)))
        row = await db.fetchone()
        subject_code = row["text"].split(" ", 1)[0]

        # get Discord API python objects
        channel = self.bot.get_channel(payload.channel_id)
        guild = channel.guild
        message = await channel.fetch_message(payload.message_id)
        reaction = core.utils.get(
            message.reactions, key=lambda react: str(react) == str(payload.emoji))
        user = guild.get_member(payload.user_id)

        NEED_REACTIONS = 5
        if event_type == "REACTION_ADD":
            # wait in queue
            if reaction.count <= NEED_REACTIONS:
                need_more = (NEED_REACTIONS + 1) - reaction.count
                embed = Embed(
                    description=f"Díky za zájem o {subject_code} {user.mention}. Uživatel přidán na čekací listinu, čekáte ještě na {need_more} studenty.", color=Color.green())
                await channel.send(embed=embed, delete_after=5)

            # add the subject
            else:
                embed = Embed(
                    description=f"Předmět {subject_code} úspěšně zapsán studentem {user.mention}.", color=Color.green())
                await channel.send(embed=embed, delete_after=5)

                rep_channel = self.channel_cache.get(row["rep_channel_id"])
                if rep_channel is None:
                    rep_channel = self.bot.get_channel(row["rep_channel_id"])

                if rep_channel is None:
                    rep_channel = await guild.create_text_channel(
                        name=row["text"],
                        position=int(payload.emoji.name.lstrip("num")) - 1,
                        category=self.bot.get_channel(row["rep_category_id"])
                    )
                    row["rep_channel_id"] = rep_channel.id
                self.channel_cache[row["rep_channel_id"]] = rep_channel

                await db.execute("""
                    UPDATE reactionmenu_options
                    SET rep_channel_id = %s
                    WHERE message_id = %s AND emoji = %s
                """, (rep_channel.id, payload.message_id, str(payload.emoji)))
                await db.commit()

                async for reactor in reaction.users():
                    await rep_channel.set_permissions(reactor, read_messages=True)

        elif event_type == "REACTION_REMOVE":
            # still in queue
            if reaction.count < NEED_REACTIONS:
                embed = Embed(
                    description=f"Uživatel {user.mention} uspěšně odstráněn z čekací listiny na předmět {subject_code}.", color=Color.green())
                await channel.send(embed=embed, delete_after=5)

            # remove the subject
            else:
                embed = Embed(
                    description=f"Předmět {subject_code} úspěšně odepsán studentem {user.mention}.", color=Color.green())
                await channel.send(embed=embed, delete_after=5)

                rep_channel = self.channel_cache.get(row["rep_channel_id"])
                if rep_channel is None:
                    rep_channel = self.bot.get_channel(row["rep_channel_id"])

                if rep_channel is not None:
                    await rep_channel.set_permissions(user, read_messages=False)

        # --[]

        self.users_on_cooldown[payload.user_id] = datetime.now()

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
        self.bot.readyCogs[self.__class__.__name__] = False

        # load channels into memory for faster checks
        await db.execute("""
            SELECT DISTINCT channel_id, deleted_at
            FROM reactionmenu
            WHERE deleted_at IS NULL
        """)
        rows = await db.fetchall()
        self.in_channels = set(row["channel_id"] for row in rows)

        self.bot.readyCogs[self.__class__.__name__] = True


def setup(bot):
    bot.add_cog(Reactionmenu(bot))
