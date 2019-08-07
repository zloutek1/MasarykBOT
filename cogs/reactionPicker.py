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
from core.utils.checks import needs_database


class ReactionPicker(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @group(name='reactionmenu', aliases=('rolemenu', 'rlm'), invoke_without_command=True)
    @has_permissions(manage_channels=True)
    @needs_database
    async def reactionmenu_group(self, ctx):
        pass

    @reactionmenu_group.command(name='create', aliases=('add', 'c', 'a'))
    async def reactionmenu_create(self, ctx, *, name: str):
        try:
            await ctx.message.delete()
        except:
            pass

        name = name.lower()

        guild = ctx.guild
        channel = ctx.channel
        message = await ctx.send(f"**Reactionmenu {name}:**")

        try:
            ctx.db.execute("INSERT INTO reactionmenu (channel_id, message_id, name) VALUES (%s, %s, %s)", (channel.id, message.id, name))
            ctx.db.commit()

            for role in guild.roles:
                await channel.set_permissions(role,
                                              add_reactions=False,
                                              send_messages=False)

            await channel.set_permissions(self.bot.user,
                                          add_reactions=True,
                                          send_messages=True)
        except Exception as e:
            await message.delete()
            raise e

    @reactionmenu_group.group(name='section', aliases=('sec',), invoke_without_command=True)
    async def reactionmenu_section_group(self, ctx):
        pass

    async def get_reactionmenu(self, ctx, by_mame: str = None):
        by_mame = by_mame.lower() if by_mame is not None else None

        ctx.db.execute("SELECT * FROM reactionmenu WHERE channel_id = %s", (ctx.channel.id,))
        reactionmenus = ctx.db.fetchall()

        if len(reactionmenus) == 0:
            await ctx.send("You need to create a reactionmenu first", delete_after=5)
            return False

        if by_mame is None and len(reactionmenus) > 1:
            await ctx.send("You need to specify the name of the reactionmenu, since more exist", delete_after=5)
            return False

        reactionmenu = core.utils.get(reactionmenus, name=by_mame) if by_mame is not None else reactionmenus[0]

        return reactionmenu

    @reactionmenu_section_group.command(name='create', aliases=('add', 'c', 'a'))
    async def section_create(self, ctx, *, name: str, to_reactionmenu: str = None):
        # message ::: name: str, to_reactionmenu: str = None
        if "to_reactionmenu" in name or "to_rolemenu" in name:
            regex = r"(?:to_reactionmenu|to_rolemenu)\s*\=\s*(.*)"
            to_reactionmenu = re.search(regex, name).group(1).strip()

            regex = r"(.+?)(?=to_reactionmenu|to_rolemenu|$)"
            name = re.search(regex, name).group(1).strip()

        try:
            await ctx.message.delete()
        except:
            pass

        name = name.upper()

        if len(name) > 11:
            await ctx.send("section name can be up to 11 letters long", delete_after=5)
            return

        guild = ctx.guild
        channel = ctx.channel

        # get image
        reactionmenu = await self.get_reactionmenu(ctx, to_reactionmenu)
        if not reactionmenu:
            return

        # send image
        filename = f"assets/{reactionmenu['name']}-{name}.png"
        image = self.generate_section_image(name)
        image.save(filename)
        msg = await ctx.send(file=File(filename, filename=f"{image}.png"))
        os.remove(filename)

        # save section to db
        try:
            ctx.db.execute("INSERT INTO reactionmenu_section (reactionmenu_id, message_id, `text`) VALUES (%s, %s, %s)", (reactionmenu["id"], msg.id, name))
        except Exception as e:
            await msg.delete()
            raise e

        # send 4 messages
        messages = []
        opt_msgs = []
        for i in range(4):
            opt_msg = await ctx.send("_ _")
            messages.append((opt_msg.id,))
            opt_msgs.append(opt_msg)

        try:
            category = core.utils.get(guild.categories, name=name)
            if not category:
                perms = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    self.bot.user: discord.PermissionOverwrite(read_messages=True)
                }
                category = await guild.create_category(name, overwrites=perms)

                ctx.db.execute("INSERT INTO category (guild_id, id, name, position) VALUES (%s, %s, %s, %s)  ON DUPLICATE KEY UPDATE id=id", (category.guild.id, category.id, category.name, category.position))
                ctx.db.commit()

            # save each message to db
            ctx.db.executemany("INSERT INTO reactionmenu_section_option (section_id, message_id) VALUES (LAST_INSERT_ID(), %s)", messages)
            ctx.db.commit()

        except Exception as e:
            ctx.db.execute("DELETE FROM reactionmenu_section WHERE reactionmenu_id = %s AND message_id = %s AND `text` = %s", (reactionmenu["id"], msg.id, name))
            ctx.db.commit()

            await msg.delete()
            for msg in opt_msgs:
                await msg.delete()
            raise e

    @reactionmenu_section_group.command(name='delete', aliases=('remove', 'del', 'rm'))
    async def section_delete(self, ctx, *, name: str, from_reactionmenu: str = None):
        # message ::: name: str, to_reactionmenu: str = None
        if "from_reactionmenu" in name or "from_rolemenu" in name:
            regex = r"(?:from_reactionmenu|from_rolemenu)\s*\=\s*(.*)"
            from_reactionmenu = re.search(regex, name).group(1).strip()

            regex = r"(.+?)(?=from_reactionmenu|from_rolemenu|$)"
            name = re.search(regex, name).group(1).strip()

        try:
            await ctx.message.delete()
        except:
            pass

        name = name.upper()

        guild = ctx.guild
        channel = ctx.channel

        ctx.db.execute("SELECT * FROM `reactionmenu_section` WHERE `text` LIKE %s", (name,))
        section_row = ctx.db.fetchone()

        msg = await channel.fetch_message(section_row["message_id"])

        ctx.db.execute("""
            SELECT sec.text AS section_name, opt.text AS `text`
            FROM reactionmenu_section AS sec INNER JOIN
            reactionmenu_section_option AS rso ON sec.id=rso.section_id INNER JOIN
            reactionmenu_option AS opt ON rso.message_id = opt.message_id
            WHERE sec.id = %s""", (section_row["id"],))
        rows = ctx.db.fetchall()

        for row in rows:
            await self.option_delete.callback(self, ctx, text=row["text"], from_section=row["section_name"])
        await msg.delete()

        ctx.db.execute("SELECT * FROM `reactionmenu_section_option` WHERE section_id = %s", (section_row["id"],))
        rows = ctx.db.fetchall()

        for row in rows:
            message = channel.fetch_message(row["message_id"])
            await message.delete()


        category = core.utils.get(guild.categories, name=name)
        if category and not category.channels:
            await category.delete()

        elif category:
            await ctx.send("```ERROR :: Category still contains channels```", delete_after=5)

    @reactionmenu_group.group(name='option', aliases=('opt', 'o'), invoke_without_command=True)
    async def reactionmenu_option_group(self, ctx):
        pass

    async def get_section(self, ctx, by_mame: str = None, in_menu: str = None):
        by_mame = by_mame.upper() if by_mame is not None else None
        in_menu = in_menu.lower() if in_menu is not None else None

        reactionmenu = await self.get_reactionmenu(ctx, in_menu)
        if not reactionmenu:
            return False

        ctx.db.execute("SELECT * FROM reactionmenu_section WHERE reactionmenu_id = %s", (reactionmenu["id"],))
        sections = ctx.db.fetchall()

        if len(sections) == 0:
            await ctx.send("You need to create a section first", delete_after=5)
            return False

        if by_mame is None and len(sections) > 1:
            await ctx.send("You need to specify the name of the section, since more exist", delete_after=5)
            return False

        section = core.utils.get(sections, text=by_mame) if by_mame is not None else sections[0]

        return section

    @reactionmenu_option_group.command(name='create', aliases=('add', 'c', 'a'))
    async def option_create(self, ctx, *, text: str, to_section: str = None, to_reactionmenu: str = None):
        if "to_section" in text or "to_reactionmenu" in text or "to_rolemenu" in text:
            regex = r"to_section\s*\=\s*(.+?)(?=to_reactionmenu|to_rolemenu|$)"
            to_section = re.search(regex, text)
            to_section = to_section.group(1).strip() if to_section is not None else None

            regex = r"(?:to_reactionmenu|to_rolemenu)\s*\=\s*(.+?)(?=to_section|$)"
            to_reactionmenu = re.search(regex, text)
            to_reactionmenu = to_reactionmenu.group(1).strip() if to_reactionmenu is not None else None

            regex = r"(.+?)(?=to_reactionmenu|to_rolemenu|to_section|$)"
            text = re.search(regex, text).group(1).strip()

        try:
            await ctx.message.delete()
        except:
            pass

        guild = ctx.guild
        channel = ctx.channel

        section = await self.get_section(ctx, to_section, to_reactionmenu)
        if not section:
            return

        # select data from db
        ctx.db.execute("SELECT * FROM reactionmenu_section_option WHERE section_id = %s AND NOT is_full ORDER BY order_id", (section["id"],))
        messages = ctx.db.fetchall()

        msg = await channel.fetch_message(messages[0]["message_id"])
        content = msg.content if msg.content != "_ _" else ""
        new_content = ""

        emoji = discord.utils.get(self.bot.emojis, name=f"num{section['options']+1}")
        option_text = f"{emoji} {text}"
        if len(content) + len(option_text) < 2000 and content.count("\n") + 1 < 10:
            new_content = content + f"\n{option_text}"

        else:
            ctx.db.execute("UPDATE reactionmenu_section_option SET is_full=1 WHERE section_id = %s AND message_id = %s", (section["id"], messages[0]["message_id"]))

            if len(messages) <= 1:
                return

            msg = await channel.fetch_message(messages[1]["message_id"])
            new_content = option_text
            content = new_content

        await msg.edit(content=new_content)
        await msg.add_reaction(emoji)

        ctx.db.execute("INSERT INTO reactionmenu_option (message_id, emoji, `text`) VALUES (%s, %s, %s)", (msg.id, str(emoji), text))
        ctx.db.commit()

        chnl = core.utils.get(guild.channels, name=text)
        category = core.utils.get(guild.categories, name=section["text"])
        if not chnl:
            chnl = await guild.create_text_channel(text, category=category)

            ctx.db.execute("INSERT INTO channel (guild_id, category_id, id, name, position) VALUES (%s, %s, %s, %s, %s)  ON DUPLICATE KEY UPDATE id=id", (chnl.guild.id, category.id, chnl.id, chnl.name, chnl.position))
            ctx.db.commit()

    @reactionmenu_option_group.command(name='delete', aliases=('remove', 'del', 'rm'))
    async def option_delete(self, ctx, *, text: str, from_section: str = None, from_reactionmenu: str = None):
        if "from_section" in text or "from_reactionmenu" in text or "from_rolemenu" in text:
            regex = r"from_section\s*\=\s*(.+?)(?=from_reactionmenu|from_rolemenu|$)"
            from_section = re.search(regex, text)
            from_section = from_section.group(1).strip() if from_section else None

            regex = r"(?:to_reactionmenu|to_rolemenu)\s*\=\s*(.+?)(?=to_section|$)"
            from_reactionmenu = re.search(regex, text)
            from_reactionmenu = from_reactionmenu.group(1).strip() if from_reactionmenu else None

            regex = r"(.+?)(?=from_reactionmenu|from_rolemenu|from_section|$)"
            text = re.search(regex, text).group(1).strip()

        try:
            await ctx.message.delete()
        except:
            pass

        guild = ctx.guild
        channel = ctx.channel

        section = await self.get_section(ctx, from_section, from_reactionmenu)
        if not section:
            return

        ctx.db.execute("SELECT * FROM `reactionmenu_option` INNER JOIN reactionmenu_section_option USING (message_id) WHERE section_id = %s AND `text` LIKE %s", (section["id"], text))
        row = ctx.db.fetchone()

        msg = await channel.fetch_message(row["message_id"])
        content = msg.content

        if text not in content:
            await ctx.send("```ERROR :: option not found```")
            return

        span = re.search(r".*\n?(.*{}.*)\n?.*".format(text), content).span(1)
        new_content = content[:span[0]] + content[span[1]:]

        emoji_name = re.search(r"\:(num\d+)\:", row["emoji"]).group(1)
        emoji = discord.utils.get(self.bot.emojis, name=emoji_name)

        reaction = core.utils.get(msg.reactions, emoji=emoji)
        async for user in reaction.users():
            await msg.remove_reaction(emoji, user)
        await msg.edit(content=new_content)

        chnl = core.utils.get(guild.channels, name=text.lower().replace(" ", "-"))
        if chnl and not chnl.last_message_id:
            await chnl.delete()

        elif chnl:
            await ctx.send("```ERROR :: Failed to remove channel since it contains messages```", delete_after=5)

        ctx.db.execute("DELETE FROM reactionmenu_option WHERE id=%s", (row["id"],))
        ctx.db.commit()

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

    @reactionmenu_group.command(name="setup")
    async def setup(self, ctx, filepath: str, reactionmenu_name: str):
        try:
            await ctx.delete()
        except:
            pass

        if not os.path.isfile(filepath):
            await ctx.send(f"```ERROR :: file does not exist at {filepath}```", delete_after=5)
            return

        if os.path.splitext(filepath)[1] != ".json":
            await ctx.send(f"```ERROR :: expected a json file but got {filepath}```", delete_after=5)
            return

        with open(filepath, 'r', encoding="utf-8") as file:
            data = json.load(file)

            await self.reactionmenu_create.callback(self, ctx, name=reactionmenu_name)

            for section_name in data["sections"]:
                await self.section_create.callback(self, ctx, name=section_name, to_reactionmenu=reactionmenu_name)

                for option_text in data["sections"][section_name]:
                    await self.option_create.callback(self, ctx, text=option_text, to_section=section_name, to_reactionmenu=reactionmenu_name)

    """
    async def get_channel(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        author = guild.get_member(payload.user_id)
        emoji = payload.emoji

        if author is self.bot.user or author.bot:
            return

        self.bot.db.execute(\"""
            SELECT message_id FROM reactionmenu UNION
            SELECT message_id FROM reactionmenu_section UNION
            SELECT message_id FROM reactionmenu_section_option UNION
            SELECT message_id FROM reactionmenu_option\""")
        rows = self.bot.db.fetchall()
        ids = [row["message_id"] for row in rows]

        if payload.message_id not in ids:
            return

        if not re.match(r"num(\d+)", emoji.name):
            await message.remove_reaction(emoji, author)
            return

        self.bot.db.execute("SELECT `text` FROM reactionmenu_option WHERE message_id=%s AND emoji=%s", (message.id, str(emoji)))
        text = self.bot.db.fetchone()["text"]
        text = text.lower().replace(" ", "-")

        chnl = core.utils.get(guild.channels, name=text)
        return chnl

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # check database connection
        if not self.bot.db:
            return

        guild = self.bot.get_guild(payload.guild_id)
        author = guild.get_member(payload.user_id)
        channel = await self.get_channel(payload)

        if channel is None:
            return

        await channel.set_permissions(author, read_messages=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # check database connection
        if not self.bot.db:
            return

        guild = self.bot.get_guild(payload.guild_id)
        author = guild.get_member(payload.user_id)
        channel = await self.get_channel(payload)

        if channel is None:
            return

        await channel.set_permissions(author, read_messages=False)
    """


def setup(bot):
    bot.add_cog(ReactionPicker(bot))
    print("Cog loaded: ReactionPicker")
