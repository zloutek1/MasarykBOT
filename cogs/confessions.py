import discord
from discord.ext import commands

import core.utils.get
from random import randint


class Confessions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="confession", aliases=("confess", "confessions", "confesses"))
    async def confession_group(self, ctx):
        pass

    @confession_group.command(name="setup")
    async def confessions_setup(self, ctx, *, section_name="confessions"):
        guild = ctx.guild

        category = await guild.create_category(section_name)
        await self.bot.trigger_event("on_guild_channel_create", category)

        ###
        # Create confess channel to send messages to
        ###
        perms = {
            guild.default_role: discord.PermissionOverwrite(send_messages=True, add_reactions=False),
            self.bot.user: discord.PermissionOverwrite(send_messages=True)
        }
        confess_channel = await guild.create_text_channel("confess", category=category, overwrites=perms, slowmode_delay=600)
        await self.bot.trigger_event("on_guild_channel_create", confess_channel)

        BLANK_emoji = core.utils.get(self.bot.emojis, name="BLANK")
        await confess_channel.send("""
        {BLANK} {BLANK} {BLANK} {BLANK} {BLANK} {BLANK} {BLANK} {BLANK}

        :warning: Do not send random, pointless messages

        :warning: Do not harass anyone

        :warning: You can only send a confession to the confessions channel once every 10 minutes

        :point_down: Send Your Confessions Here :point_down:""".format(BLANK=BLANK_emoji))

        ###
        # Create confession channel to see anonymous confession in
        ###
        perms = {
            guild.default_role: discord.PermissionOverwrite(send_messages=False),
            self.bot.user: discord.PermissionOverwrite(send_messages=True)
        }
        confession_channel = await guild.create_text_channel("confession", category=category, overwrites=perms)
        await self.bot.trigger_event("on_guild_channel_create", confession_channel)

    @commands.Cog.listener()
    async def on_message(self, message):
        channel = message.channel
        if channel.name != "confess" or message.author.bot:
            return

        await message.delete()

        embed = discord.Embed(
            title="Confession",
            description=message.content,
            color=discord.Color.from_rgb(
                randint(0, 255), randint(0, 255), randint(0, 255))
        )
        embed.set_footer(text="All confessions are anonymous.")

        confession_channel = core.utils.get(
            message.guild.text_channels, name="confession")
        if confession_channel:
            await confession_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Confessions(bot))
