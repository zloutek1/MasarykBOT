import discord
from discord.ext import commands
from discord.ext.commands import Bot, has_permissions
from discord import Color, Embed, Member, File, Role, Emoji, PartialEmoji

import core.utils.get
from core.utils.checks import safe


class TransitionToMUNI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @has_permissions(administrator=True)
    async def init_transition(self, ctx):
        await self.init_aboutmenu(ctx)
        await self.init_rules(ctx)

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

        roles = [ctx.get_role("light"), ctx.get_role("dark")]
        emojis = ["🌕", "🌑"]
        await aboutmenu_create.callback(cog, ctx,
                                        "light-dark.jpg", roles, emojis,
                                        text="Light mode vs Dark mode")

        roles = [ctx.get_role("bot development"), ctx.get_role(
            "NSFW"), ctx.get_role("anime"), ctx.get_role("entertainment")]
        emojis = [ctx.get_emoji("bot_tag"), ctx.get_emoji(
            "warning~1"), ctx.get_emoji("an_chika"), "🍿"]
        await aboutmenu_create.callback(cog, ctx,
                                        "bot-nsfw-weeb-entertainment.png", roles, emojis,
                                        text="Bot development / NSFW content / Anime and Manga talk / Entertainment (books, movies, ...)")

        roles = [ctx.get_role("dank memer"), ctx.get_role("rythm")]
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

        rules_channel = core.utils.get(ctx.guild.channels, name="pravidla")
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


def setup(bot):
    bot.add_cog(TransitionToMUNI(bot))
