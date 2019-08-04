import discord
from discord.ext import commands
from discord import Colour, Embed, Member, Object, File

import core.utils.get
from core.utils.checks import needs_database


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="verification")
    @needs_database
    async def verication_group(self, ctx):
        pass

    @verication_group.command(name="setup")
    async def verification_setup(self, ctx, message_id: int):
        await ctx.message.delete()

        guild = ctx.guild
        channel = ctx.channel
        message = await channel.fetch_message(message_id)

        ctx.db.execute("INSERT INTO verification_channel (guild_id, channel_id, message_id, emoji) VALUES (%s, %s, %s, %s)", (guild.id, channel.id, message.id, emoji.name))

        await message.add_reaction(core.utils.get(self.bot.emojis, name="Verification"))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # check database connection
        if not self.bot.db:
            return

        guild = self.bot.get_guild(payload.guild_id)
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        author = guild.get_member(payload.user_id)
        emoji = payload.emoji

        if author.bot:
            return

        self.bot.db.execute("SELECT * FROM verification_channel WHERE (guild_id = %s AND channel_id = %s)", (guild.id, channel.id))
        rows = self.bot.db.fetchall()

        row = core.utils.get(rows, message_id=message.id)
        if not row:
            return

        if emoji.name != row["emoji"]:
            await message.remove_reaction(emoji, author)
            return

        studentRole = core.utils.get(guild.roles, name="Student")
        await author.add_roles(studentRole)

        # -- send DM with detail how to verify yourself

        embed = Embed(
            title=f"Welcome to {guild.name} discord",
            description="*Before you go, could you please verify yourself as a student of MUNI? We would appreciate it, but it is not a requirement to enter*",
            color=0x000000
        )

        await author.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # check database connection
        if not self.bot.db:
            return

        guild = self.bot.get_guild(payload.guild_id)
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        author = guild.get_member(payload.user_id)
        emoji = payload.emoji

        if author.bot:
            return

        self.bot.db.execute("SELECT * FROM verification_channel WHERE (guild_id = %s AND channel_id = %s)", (guild.id, channel.id))
        rows = self.bot.db.fetchall()

        row = core.utils.get(rows, message_id=message.id)
        if not row:
            return

        if emoji.name == row["emoji"]:
            studentRole = core.utils.get(guild.roles, name="Student")
            await author.remove_roles(studentRole)


def setup(bot):
    bot.add_cog(Verification(bot))
    print("Cog loaded: Verification")
