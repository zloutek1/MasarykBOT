import discord
from discord.ext import commands
from discord.ext.commands import Bot, has_permissions
from discord import Color, Embed, Member, File, Role, Emoji, PartialEmoji

import json

import core.utils.get
from core.utils.checks import needs_database, safe
from core.utils.db import Database


class TransitionToMUNI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @has_permissions(administrator=True)
    async def init_transition(self, ctx):
        await self.init_rules(ctx)
        await self.init_aboutmenu(ctx)
        await self.init_reactionmenu(ctx)

        await safe(ctx.message.delete)()

    async def init_aboutmenu(self, ctx):
        #
        # Aboutmenu
        ##################

        guild = ctx.guild
        channel = ctx.channel

        chnl = ctx.get_channel("about-you")
        if not chnl:
            chnl = await guild.create_text_channel("about-you")

        elif chnl.last_message_id:
            await ctx.send(f"[Aboutmenu] {chnl.mention} not empty. Skipping")
            return False

        cog = self.bot.get_cog("Aboutmenu")
        aboutmenu_create = self.bot.get_command("aboutmenu create")
        ctx.channel = chnl

        roles = [("light", Color(0xe4e4e4)),
                 ("dark", Color(0x000001))]
        for i, role in enumerate(roles):
            r = ctx.get_role(role[0])
            if r:
                roles[i] = r
            else:
                roles[i] = await guild.create_role(name=role[0], color=role[1])
        # roles = [ctx.get_role("light"), ctx.get_role("dark")]

        emojis = ["🌕", "🌑"]
        await aboutmenu_create.callback(cog, ctx,
                                        "light-dark.jpg", roles, emojis,
                                        text="Light mode vs Dark mode")

        roles = [("bot development", Color.blue()),
                 ("NSFW", Color(0x000001)),
                 ("anime", Color(0xdb6565)),
                 ("entertainment", Color.green())]
        for i, role in enumerate(roles):
            r = ctx.get_role(role[0])
            if r:
                roles[i] = r
            else:
                roles[i] = await guild.create_role(name=role[0], color=role[1])

        # roles = [ctx.get_role("bot development"), ctx.get_role(
        #    "NSFW"), ctx.get_role("anime"), ctx.get_role("entertainment")]
        emojis = [ctx.get_emoji("bot_tag"), ctx.get_emoji(
            "warning"), ctx.get_emoji("an_chika"), "🍿"]
        await aboutmenu_create.callback(cog, ctx,
                                        "bot-nsfw-weeb-entertainment.png", roles, emojis,
                                        text="Bot development / NSFW content / Anime and Manga talk / Entertainment (books, movies, ...)")

        roles = [("dank memer", Color.dark_green()),
                 ("rythm", Color.default())]
        for i, role in enumerate(roles):
            r = ctx.get_role(role[0])
            if r:
                roles[i] = r
            else:
                roles[i] = await guild.create_role(name=role[0], color=role[1])
        #roles = [ctx.get_role("dank memer"), ctx.get_role("rythm")]
        emojis = [ctx.get_emoji("dank_memer"), ctx.get_emoji("rythm")]
        await aboutmenu_create.callback(cog, ctx,
                                        "memer-rythm.png", roles, emojis,
                                        text="Dank memer bot / Rythm bot")

        ctx.channel = channel
        return True

    async def init_rules(self, ctx):
        #
        # Rules
        ##################

        guild = ctx.guild
        channel = ctx.channel

        rules_channel = ctx.get_channel("pravidla")
        if not rules_channel:
            rules_channel = await ctx.guild.create_text_channel("pravidla")

        elif rules_channel.last_message_id:
            await ctx.send(f"[Rules] {rules_channel.mention} not empty. Skipping")
            return False

        cog = self.bot.get_cog("Rules")
        setup_rules = self.bot.get_command("rules setup")
        ctx.channel = rules_channel
        await setup_rules.callback(cog, ctx)

        ctx.channel = channel
        return True

    @needs_database
    async def init_reactionmenu(self, ctx, *, db=Database()):
        #
        # Reactionmenu
        ##################
        guild = ctx.guild
        channel = ctx.channel

        menu_channel = ctx.get_channel("vyber-predmetov")
        if not menu_channel:
            menu_channel = await ctx.guild.create_text_channel("vyber-predmetov")

        elif menu_channel.last_message_id:
            await ctx.send(f"[Reactionmenu] {menu_channel.mention} not empty. Skipping")
            return False

        cog = self.bot.get_cog("Reactionmenu")
        reactionmenu_create = self.bot.get_command("reactionmenu create")
        option_add = self.bot.get_command("reactionmenu option add")
        ctx.channel = menu_channel

        # load data
        with open("assets/vyber-predmetov.json") as fileR:
            data = json.load(fileR)

        for section, options in data["sections"].items():
            print("creating section", section, "with", len(options), "options")
            # create menu
            menu_id = await reactionmenu_create.callback(cog, ctx, name=section)
            if not menu_id:
                await ctx.send("[Reactionmenu] Error while creating section")
                continue

            # get reactionmenu
            await db.execute("""
                SELECT * FROM reactionmenu
                WHERE message_id = %s
                LIMIT 1
            """, (menu_id,))
            reactionmenu_db = await db.fetchone()

            # parse options
            for i, option in enumerate(options):
                await option_add.callback(cog, ctx, menu_id, text=option)

                # channel already exists? get it
                code = option.split(" ", 1)[0].lower()
                chnls = list(filter(lambda ch: ch.name.startswith(
                    code), guild.text_channels))
                if not chnls:
                    continue

                category = guild.get_channel(
                    reactionmenu_db["rep_category_id"])

                for ch in chnls:
                    await ch.edit(
                        category=category,
                        position=i
                    )

        ctx.channel = channel
        return True


def setup(bot):
    bot.add_cog(TransitionToMUNI(bot))
