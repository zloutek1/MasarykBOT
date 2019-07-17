from discord import Colour, Embed, Member, Object, File
import discord.utils
from discord.ext import commands
from discord.ext.commands import Bot, Converter, group

from cogs.utils.db import DuplicateEntryError

from PIL import Image, ImageDraw, ImageFont
import os
import json


class ReactionPicker(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @group(name='rolemenu', hidden=True, invoke_without_command=True)
    async def rolemenu_group(self, ctx):
        pass

    @rolemenu_group.group(name='section')
    async def section_group(self, ctx):
        pass

    @section_group.command(name='setup')
    async def section_setup(self, ctx, filepath: str):
        await ctx.message.delete()

        database_sections = tuple()
        database_relations = tuple()
        database_options = tuple()

        try:
            with open('assets/' + filepath, 'r') as fp:
                data = json.load(fp)

                guild_id = data["guild"]
                channel = self.bot.get_channel(data["channel"])

                if channel is None:
                    await ctx.send("```Error: unknown channel, please look into the config file```")
                    return

                for section_order, section_text in enumerate(data["sections"]):
                    img = self.generate_section_image(section_text)
                    img.save("assets/section.png")
                    section_msg = await ctx.send(file=File("assets/section.png", filename=f"{section_text}.png"))
                    database_sections += ((guild_id, channel.id, section_msg.id, section_order, section_text),)

                    """
                    batch_order = 0
                    option_order = 0
                    is_full = False
                    for predmet in predmety:
                        if len(batch) + len(predmet) < 2000 and option_order < 10:
                            emoji = discord.utils.get(self.bot.emojis, name=f"num{option_order}")
                            batch += f"{emoji} {predmet}\n"
                            database_options += ((guild_id, channel.id, None, f"{emoji} {predmet}\n"),)
                            option_order += 1
                            is_full = False
                        else:
                            bulk_msg = await ctx.send(batch)
                            database_relations += ((section_msg.id, bulk_msg.id),)

                            for option_order in range(option_order):
                                emoji = discord.utils.get(self.bot.emojis, name=f"num{option_order}")
                                await bulk_msg.add_reaction(emoji)

                            batch_order += 1
                            option_order = 0
                            is_full = True
                            batch = ""
                    else:
                        if not is_full:
                            option_msg = await ctx.send(batch)
                            database_options += ((guild_id, channel.id, option_msg.id, batch_order),)
                            database_relations += ((section_msg.id, option_msg.id),)

                            for option_order in range(option_order):
                                emoji = discord.utils.get(self.bot.emojis, name=f"num{option_order}")
                                await option_msg.add_reaction(emoji)
                    """

                    batch = ""
                    predmety = data["sections"][section_text]
                    bulk_order = 0
                    option_order = 0
                    is_full = False

                    if len(predmety) == 0:
                        continue

                    bulk_message = await ctx.send("**No options**")
                    for predmet in predmety:
                        if len(batch) + len(predmet) < 2000 and option_order < 10:
                            emoji = discord.utils.get(self.bot.emojis, name=f"num{option_order}")
                            text = f"{emoji} {predmet}"

                            batch += f"{text}\n"
                            database_options += ((guild_id, channel.id, bulk_message.id, text),)
                            option_order += 1
                            is_full = False

                        else:
                            database_relations += ((section_msg.id, bulk_message.id, bulk_order, option_order),)
                            await bulk_message.edit(content=batch)
                            bulk_message = await ctx.send("**No more options**")

                            batch = ""
                            bulk_order += 1
                            option_order = 0
                            is_full = True
                    else:
                        if not is_full:
                            database_relations += ((section_msg.id, bulk_message.id, bulk_order, option_order),)
                            await bulk_message.edit(content=batch)

                os.remove("assets/section.png")

        except OSError as e:
            await ctx.send("```" + e + "```")

        try:
            ctx.db.executemany("INSERT INTO `reactionmenu_sections` (`guild_id`, `channel_id`, `section_id`, `section_order`, `text`) VALUES (%s, %s, %s, %s, %s)", database_sections)

            print(database_options)
            ctx.db.executemany("INSERT INTO `reactionmenu_options`(`guild_id`, `channel_id`, `bulk_id`, `text`) VALUES (%s, %s, %s, %s)", database_options)

            ctx.db.executemany("INSERT INTO `reactionmenu_relations`(`section_id`, `bulk_id`, `bulk_order`, `option_order`) VALUES (%s, %s, %s, %s)", database_relations)

            ctx.db.commit()

        except DuplicateEntryError as e:
            await ctx.send(f"```Error: Values in database already exist\n{e}```")

        # !rolemenu section setup vyber-predmetov.json

    @staticmethod
    def generate_section_image(text):
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
    print("Cog loaded: Picker")
