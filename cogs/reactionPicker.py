from discord import Colour, Embed, Member, Object, File
import discord.utils
from discord.ext import commands
from discord.ext.commands import Bot, Converter, group

from config import BotConfig

from PIL import Image, ImageDraw, ImageFont
import os
import json
import re

import core.utils.get


class ReactionPicker(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @group(name='reactionmenu', aliases=('rolemenu',), invoke_without_command=True)
    async def reactionmenu_group(self, ctx):
        pass

    @reactionmenu_group.command(name='create', alias=('setup',))
    async def reactionmenu_setup(self, ctx, name: str):
        await ctx.message.delete()
        name = name.lower()

        guild = ctx.guild
        channel = ctx.channel

        ctx.db.execute("INSERT INTO reactionmenu (guild_id, channel_id, name) VALUES (%s, %s, %s)", (guild.id, channel.id, name))
        ctx.db.commit()

        await ctx.send(f"**Reactionmenu {name}:**")

    @reactionmenu_group.group(name='section', invoke_without_command=True)
    async def reactionmenu_section_group(self, ctx):
        pass

    async def get_reactionmenu(self, ctx, by_mame: str):
        by_mame = by_mame.lower()

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

    @reactionmenu_section_group.command(name='create', aliases=('add',))
    async def section_setup(self, ctx, *, name: str, to_reactionmenu: str = None):
        # message ::: name: str, to_reactionmenu: str = None
        if "to_reactionmenu" in name or "to_rolemenu" in name:
            regex = r"(?:to_reactionmenu|to_rolemenu)\s*\=\s*(.*)"
            to_reactionmenu = re.search(regex, name).groups(1).strip()

            regex = r"(.+?)(?=to_reactionmenu|to_rolemenu|$)"
            name = re.search(regex, name).groups(1).strip()

        await ctx.message.delete()
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

        # save each message to db
        ctx.db.executemany("INSERT INTO reactionmenu_section_option (section_id, message_id) VALUES (LAST_INSERT_ID(), %s)", messages)
        ctx.db.commit()

    @reactionmenu_group.group(name='option', invoke_without_command=True)
    async def reactionmenu_option_group(self, ctx):
        pass

    async def get_section(self, ctx, by_mame: str = None, in_menu: str = None):
        by_mame = by_mame.upper()
        in_menu = in_menu.lower()

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

    @reactionmenu_option_group.command(name='create', aliases=('add',))
    async def option_setup(self, ctx, *, text: str, to_section: str = None, to_reactionmenu: str = None):
        if "to_section" in text or "to_reactionmenu" in text or "to_rolemenu" in text:
            regex = r"to_section\s*\=\s*(.+?)(?=to_reactionmenu|to_rolemenu|$)"
            to_section = re.search(regex, text)
            to_section = to_section.group(1).strip() if to_section is not None else None

            regex = r"(?:to_reactionmenu|to_rolemenu)\s*\=\s*(.+?)(?=to_section|$)"
            to_reactionmenu = re.search(regex, text)
            to_reactionmenu = to_reactionmenu.group(1).strip() if to_reactionmenu is not None else None

            regex = r"(.+?)(?=to_reactionmenu|to_rolemenu|to_section|$)"
            text = re.search(regex, text).group(1).strip()

        await ctx.message.delete()

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
            msg = await channel.fetch_message(message[1]["message_id"])
            new_content = option_text

        await msg.edit(content=new_content)

        ctx.db.execute("INSERT INTO reactionmenu_option (message_id, emoji, `text`) VALUES (%s, %s, %s)", (msg.id, str(emoji), text))
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


def setup(bot):
    bot.add_cog(ReactionPicker(bot))
    print("Cog loaded: ReactionPicker")
