from discord import Colour, Embed, Member, Object, File
import discord.utils
from discord.ext import commands
from discord.ext.commands import Bot, Converter, group

from core.utils.db import DuplicateEntryError
from config import BotConfig

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

                ##
                # ASSERT That the values dont already exist
                ##
                self.bot.db.execute("""
                    SELECT * FROM `reactionmenu_sections`
                    WHERE `guild_id`={guild_id} AND `channel_id`={channel_id}
                    """.format(guild_id=data["guild"], channel_id=data["channel"]))

                if len(self.bot.db.fetchall()) != 0:
                    raise DuplicateEntryError("Error: Duplicate values in reactionmenu_sections table, cannot add reaction menu")

                self.bot.db.execute("""
                    INSERT INTO `rolememu`(`guild_id`, `channel_id`, `category_id`)
                           VALUES (%s, %s, %s)
                """, (data["guild"], data["channel"], data["category"]))

                ##
                # CREATE a section
                ##
                for section_order, section_text in enumerate(data["sections"]):
                    img = self.generate_section_image(section_text)
                    img.save("assets/section.png")
                    section_msg = await ctx.send(file=File("assets/section.png", filename=f"{section_text}.png"))
                    database_sections += ((guild_id, channel.id, section_msg.id, section_order, section_text),)

                    batch = ""
                    predmety = data["sections"][section_text]
                    bulk_order = 0
                    option_order = 0
                    is_full = False

                    if len(predmety) == 0:
                        continue

                    ##
                    # CREATE batch messages with 10 subjects
                    ##
                    bulk_message = await ctx.send("**No options**")
                    for predmet in predmety:
                        if len(batch) + len(predmet) < 2000 and option_order < 10:
                            # message can still fit into batch
                            emoji = discord.utils.get(self.bot.emojis, name=f"num{option_order}")

                            batch += f"{emoji} {predmet}\n"
                            database_options += ((guild_id, channel.id, bulk_message.id, option_order, str(emoji), predmet),)
                            database_relations += ((section_msg.id, bulk_message.id, bulk_order, option_order),)
                            option_order += 1
                            is_full = False

                            await bulk_message.add_reaction(emoji)

                        else:
                            # batch is full, send it
                            await bulk_message.edit(content=batch)
                            bulk_message = await ctx.send("**No more options**")

                            batch = ""
                            bulk_order += 1
                            option_order = 0
                            is_full = True
                    else:
                        # parsed all subjects, send the message if wasnt already
                        if not is_full:
                            await bulk_message.edit(content=batch)

                os.remove("assets/section.png")

        except OSError as e:
            await ctx.send(f"```{e}```")

        except DuplicateEntryError as e:
            await ctx.send(f"```{e}```")

        ##
        # add values to database
        ##
        try:
            ctx.db.executemany("INSERT INTO `reactionmenu_sections` (`guild_id`, `channel_id`, `section_id`, `section_order`, `text`) VALUES (%s, %s, %s, %s, %s)", database_sections)

            ctx.db.executemany("INSERT INTO `reactionmenu_options`(`guild_id`, `channel_id`, `bulk_id`,  `option_order`, `emoji`, `text`) VALUES (%s, %s, %s, %s, %s, %s)", database_options)

            ctx.db.executemany("INSERT INTO `reactionmenu_relations`(`section_id`, `bulk_id`, `bulk_order`, `option_order`) VALUES (%s, %s, %s, %s)", database_relations)

            ctx.db.commit()

        except DuplicateEntryError as e:
            await ctx.send(f"```Error: Values in database already exist\n{e}```")

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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.channel_id in BotConfig.reactionmenu_channels:

            guild = self.bot.get_guild(payload.guild_id)
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            author = guild.get_member(payload.user_id)

            ##
            # don't do anything on BOT's reactions
            ##
            if author != self.bot.user:
                option = self.get_options(guild, channel, message, payload)

                ##
                # select category where the channel will be shown or added
                ##
                self.bot.db.execute(f"""
                    SELECT  `category_id` FROM `rolememu`
                    WHERE `guild_id`= {guild.id} AND
                          `channel_id`= {channel.id}
                """)
                category_id = self.bot.db.fetchone()["category_id"]

                ##
                # create channel if not exist
                ##
                the_channel_name = "-".join(option["text"].lower().split(" "))
                the_channel = discord.utils.get(guild.channels, name=the_channel_name)
                if the_channel is None:
                    category = discord.utils.get(guild.categories, id=category_id)
                    the_channel = await guild.create_text_channel(the_channel_name, category=category)
                    await the_channel.set_permissions(guild.default_role,
                                                      read_messages=False,
                                                      read_message_history=False)

                ##
                # TODO: get order of the channel from the database
                ##

                ##
                # show the channel to the user
                ##
                await the_channel.set_permissions(author,
                                                  read_messages=True,
                                                  read_message_history=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.channel_id in BotConfig.reactionmenu_channels:

            guild = self.bot.get_guild(payload.guild_id)
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            author = guild.get_member(payload.user_id)

            ##
            # don't do anything on BOT's reactions
            ##
            if author != self.bot.user:
                option = self.get_options(guild, channel, message, payload)

                ##
                # select category where the channel will be shown or added
                ##
                self.bot.db.execute(f"""
                    SELECT  `category_id` FROM `rolememu`
                    WHERE `guild_id`= {guild.id} AND
                          `channel_id`= {channel.id}
                """)
                category_id = self.bot.db.fetchone()["category_id"]

                ##
                # get the channel
                ##
                the_channel_name = "-".join(option["text"].lower().split(" "))
                the_channel = discord.utils.get(guild.channels, name=the_channel_name)
                if the_channel is None:
                    return

                ##
                # room is completely empty
                ##
                if the_channel.last_message_id is None:
                    await the_channel.delete(reason="it was empty")
                    return

                ##
                # hide the channel from the user
                ##
                await the_channel.set_permissions(author,
                                                  read_messages=False,
                                                  read_message_history=False)

    def get_options(self, guild, channel, message, payload):
        chars_until = message.content.index(str(payload.emoji))
        option_order = message.content[:chars_until].count("\n")

        ##
        # select text of the messasge based on reaction
        ##
        self.bot.db.execute(f"""
            SELECT * FROM `reactionmenu_options` AS `opt`
               INNER JOIN `reactionmenu_relations` AS `rel`
               ON `opt`.`bulk_id` = `rel`.`bulk_id` AND
                  `opt`.`option_order` = `rel`.`option_order`
            WHERE `guild_id`= {guild.id} AND
                  `channel_id`= {channel.id} AND
                  `opt`.`bulk_id`= {message.id} AND
                  `rel`.`option_order` = {option_order}
        """)
        option = self.bot.db.fetchone()

        return option


def setup(bot):
    bot.add_cog(ReactionPicker(bot))
    print("Cog loaded: Picker")
