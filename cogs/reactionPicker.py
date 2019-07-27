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


class ReactionPicker(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @group(name='reactionmenu', aliases=('rolemenu', 'rlm'), invoke_without_command=True)
    @has_permissions(manage_channels=True)
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

        ctx.db.execute("INSERT INTO reactionmenu (guild_id, channel_id, message_id, name) VALUES (%s, %s, %s, %s)", (guild.id, channel.id, message.id, name))
        ctx.db.commit()

    @reactionmenu_group.command(name='delete', aliases=('del', 'remove', 'rm'))
    async def reactionmenu_delete(self, ctx, *, name: str):
        try:
            await ctx.message.delete()
        except:
            pass

        name = name.lower()

        guild = ctx.guild
        channel = ctx.channel

        ctx.db.execute("""SELECT DISTINCT sec.text FROM reactionmenu AS menu
            LEFT OUTER JOIN reactionmenu_section AS sec
            ON menu.id = sec.reactionmenu_id
            WHERE guild_id=%s AND channel_id=%s AND name=%s""", (guild.id, channel.id, name))
        rows = ctx.db.fetchall()

        categories = [core.utils.get(guild.categories, name=row["text"]) for row in rows]
        for category in categories:
            allEmpty = True
            for channel in category.channels:
                if channel.last_message_id is None:
                    await channel.delete()
                else:
                    allEmpty = False
            if allEmpty:
                await category.delete()

        ctx.db.execute("""SELECT DISTINCT menu.message_id as reactionmenuID, sec.message_id as sectionID, sec_opt.message_id as optionID FROM reactionmenu AS menu
            LEFT OUTER JOIN reactionmenu_section AS sec
            ON menu.id = sec.reactionmenu_id
            LEFT OUTER JOIN reactionmenu_section_option AS sec_opt
            ON sec.id = sec_opt.section_id
            LEFT OUTER JOIN reactionmenu_option AS opt
            ON sec_opt.message_id = opt.message_id
            WHERE guild_id=%s AND channel_id=%s AND name=%s""", (guild.id, channel.id, name))
        ids = ctx.db.fetchall()

        to_delete = set(val for row in ids for val in row.values())
        for msg_id in sorted(to_delete):
            try:
                message = await channel.fetch_message(msg_id)
                await message.delete()
            except:
                pass

        ctx.db.execute("TRUNCATE `reactionmenu_option`;")
        ctx.db.execute("TRUNCATE `reactionmenu_section_option`;")
        ctx.db.execute("TRUNCATE `reactionmenu_section`;")
        ctx.db.execute("TRUNCATE `reactionmenu`;")

    @reactionmenu_group.group(name='section', aliases=('sec',), invoke_without_command=True)
    async def reactionmenu_section_group(self, ctx):
        pass

    async def get_reactionmenu(self, ctx, by_mame: str = None):
        by_mame = by_mame.lower() if by_mame is not None else None

        ctx.db.execute("""
            SELECT * FROM reactionmenu WHERE
                guild_id = %s AND
                channel_id = %s""", (ctx.guild.id, ctx.channel.id))
        reactionmenus = ctx.db.fetchall()

        if len(reactionmenus) == 0:
            await ctx.send("You need to create a reactionmenu first")
            return False

        if by_mame is None and len(reactionmenus) > 1:
            await ctx.send("You need to specify the name of the reactionmenu, since more exist")
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
            await ctx.send("section name can be up to 11 letters long")
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
        ctx.db.execute("INSERT INTO reactionmenu_section (reactionmenu_id, message_id, `text`) VALUES (%s, %s, %s)", (reactionmenu["id"], msg.id, name))
        ctx.db.commit()

        # send 4 messages
        messages = []
        for i in range(4):
            opt_msg = await ctx.send("_ _")
            messages.append((opt_msg.id,))

        category = core.utils.get(guild.categories, name=name)
        if not category:
            perms = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False)
            }
            category = await guild.create_category(name, overwrites=perms)

        # save each message to db
        ctx.db.executemany("INSERT INTO reactionmenu_section_option (section_id, message_id) VALUES (LAST_INSERT_ID(), %s)", messages)
        ctx.db.commit()

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
            await ctx.send("You need to create a section first")
            return False

        if by_mame is None and len(sections) > 1:
            await ctx.send("You need to specify the name of the section, since more exist")
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
        if not os.path.isfile(filepath):
            await ctx.send(f"```ERROR :: file does not exist at {filepath}```")
            return

        if os.path.splitext(filepath)[1] != ".json":
            await ctx.send(f"```ERROR :: expected a json file but got {filepath}```")
            return

        with open(filepath, 'r', encoding="utf-8") as file:
            data = json.load(file)

            await self.reactionmenu_create.callback(self, ctx, name=reactionmenu_name)

            for section_name in data["sections"]:
                await self.section_create.callback(self, ctx, name=section_name, to_reactionmenu=reactionmenu_name)

                for option_text in data["sections"][section_name]:
                    await self.option_create.callback(self, ctx, text=option_text, to_section=section_name, to_reactionmenu=reactionmenu_name)

    async def get_channel(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        author = guild.get_member(payload.user_id)
        emoji = payload.emoji

        if author is self.bot.user or author.bot:
            return

        self.bot.db.execute("""
            SELECT message_id FROM reactionmenu UNION
            SELECT message_id FROM reactionmenu_section UNION
            SELECT message_id FROM reactionmenu_section_option UNION
            SELECT message_id FROM reactionmenu_option""")
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
        guild = self.bot.get_guild(payload.guild_id)
        author = guild.get_member(payload.user_id)
        channel = await self.get_channel(payload)

        if channel is None:
            return

        await channel.set_permissions(author, read_messages=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        author = guild.get_member(payload.user_id)
        channel = await self.get_channel(payload)

        if channel is None:
            return

        await channel.set_permissions(author, read_messages=False)


def setup(bot):
    bot.add_cog(ReactionPicker(bot))
    print("Cog loaded: ReactionPicker")
