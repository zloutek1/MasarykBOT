import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord import Color, Embed, Permissions

import json

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

        await self.bot.trigger_event("on_ready")
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
            await ctx.send(f"[Aboutmenu] {chnl.mention} not empty. Skipping", delete_after=5)
            return False

        cog = self.bot.get_cog("Aboutmenu")
        aboutmenu_create = self.bot.get_command("aboutmenu create")
        ctx.channel = chnl

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

    @needs_database
    async def init_rules(self, ctx, *, db: Database = None):
        #
        # Rules
        ##################

        channel = ctx.channel

        rules_channel = ctx.get_channel("pravidla")
        if not rules_channel:
            rules_channel = await ctx.guild.create_text_channel("pravidla")

        elif rules_channel.last_message_id:
            await ctx.send(f"[Rules] {rules_channel.mention} not empty. Skipping", delete_after=5)
            return False

        cog = self.bot.get_cog("Rules")
        setup_rules = self.bot.get_command("rules setup")
        ctx.channel = rules_channel
        await setup_rules.callback(cog, ctx)

        verified_role = ctx.get_role("Student")
        if not verified_role:
            perms = Permissions()
            perms.read_messages = True

            verified_role = await ctx.guild.create_role(
                name="Student",
                color=Color(0x9cadb8),
                permissions=perms)

        await db.execute("""
            INSERT INTO verification
                (channel_id, verified_role_id)
            VALUES (%s, %s)
        """, (rules_channel.id, verified_role.id))
        await db.commit()

        cog = self.bot.get_cog("Verification")
        add_verification = self.bot.get_command("add_verification_message")
        await add_verification.callback(cog, ctx, rules_channel.id)

        ctx.channel = channel
        return True

    @needs_database
    async def init_reactionmenu(self, ctx, *, db: Database = None):
        #
        # Reactionmenu
        ##################
        guild = ctx.guild
        channel = ctx.channel

        menu_channel = ctx.get_channel("předměty")
        if not menu_channel:
            menu_channel = await ctx.guild.create_text_channel("předměty")
            await self.bot.trigger_event("on_guild_channel_create", menu_channel)

        """
        create channel for commands
        """

        menu_text_channel = ctx.get_channel("výběr-předmětů")
        if not menu_text_channel:
            menu_text_channel = await ctx.guild.create_text_channel("výběr-předmětů")
            await self.bot.trigger_event("on_guild_channel_create", menu_text_channel)

        await db.execute("INSERT INTO reactionmenu VALUES (%s, %s, NULL)", (menu_channel.id, menu_text_channel.id))
        await db.commit()

        """
        setup
        """

        async def setup_menu():
            """
            get reactionmenu cog
            """

            cog = self.bot.get_cog("Reactionmenu")
            reactionmenu_create = self.bot.get_command("reactionmenu create")
            option_add = self.bot.get_command("reactionmenu option add")
            ctx.channel = menu_channel

            # load data
            with open("assets/vyber-predmetov.json") as fileR:
                data = json.load(fileR)

            for section, options in data["sections"].items():
                # create menu
                menu_id = await reactionmenu_create.callback(cog, ctx, name=section)
                if not menu_id:
                    await ctx.send("[Reactionmenu] Error while creating section")
                    continue

                # get reactionmenu
                await db.commit()
                await db.execute("""
                    SELECT * FROM reactionmenu_sections
                    WHERE message_id = %s
                    LIMIT 1
                """, (menu_id,))
                reactionmenu_db = await db.fetchone()

                # parse options
                for i, option in enumerate(options):
                    option_id = await option_add.callback(cog, ctx, menu_id, text=option)

                    # channel already exists? get it
                    code = option.split(" ", 1)[0].lower()
                    chnls = list(filter(lambda ch: ch.name.startswith(
                        code), guild.text_channels))
                    if not chnls:
                        continue
                    ch = chnls[0]

                    category = guild.get_channel(
                        reactionmenu_db["rep_category_id"])

                    old_category = ch.category
                    await ch.edit(
                        category=category,
                        sync_permissions=True
                    )
                    if len(old_category.channels) == 0:
                        await old_category.delete()

                    await db.execute("""
                        UPDATE reactionmenu_options
                        SET rep_channel_id = %s
                        WHERE message_id = %s AND `text` LIKE %s
                    """, (ch.id, option_id, option))
                    await db.commit()

        async def setup_messages():
            """
            send first message
            """

            embed = Embed(
                description="""
                :warning: předmět si múžeš zapsat/zrušit každých 5 sekund
                příkazem `!subject add/remove <subject_code>`

                :point_down: Zapiš si své předměty zde :point_down:""".strip(),
                color=Color(0xFFD800))
            await menu_text_channel.send(embed=embed)

            await menu_text_channel.edit(slowmode_delay=5)

        if menu_channel.last_message_id:
            await ctx.send(f"[Reactionmenu] {menu_channel.mention} not empty. Skipping", delete_after=5)
        else:
            await setup_menu()

        if menu_text_channel.last_message_id:
            await ctx.send(f"[Reactionmenu] {menu_text_channel.mention} not empty. Skipping", delete_after=5)
        else:
            await setup_messages()

        ctx.channel = channel
        return True

    @commands.command()
    @has_permissions(administrator=True)
    async def resend_join_message(self, ctx):
        members = ctx.guild.members
        role = ctx.get_role("Student")
        for member in members:
            if member.bot:
                continue

            if role in member.roles:
                continue

            await member.send("""
**Vítej na discordu Fakulty Informatiky Masarykovy Univerzity v Brně**

❯ Pro vstup je potřeba přečíst #pravidla a **KLIKNOUT NA {Verification} REAKCI!!!**
❯ Když jsem {offline_tag} offline, tak ne všechno proběhne hned.
❯ Pokud nedostanete hned roli @Student, tak zkuste odkliknout, chvíli počkat a znova zakliknout.
""".format(
                Verification=ctx.get_emoji("Verification"),
                offline_tag=ctx.get_emoji("status_offline")))


def setup(bot):
    bot.add_cog(TransitionToMUNI(bot))
