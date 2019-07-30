import discord
from discord.ext import commands
from discord import Colour, Embed, Member, Object, File

import core.utils.get


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="verification")
    async def verication_group(self, ctx):
        pass

    @verication_group.command(name="setup")
    async def verification_setup(self, ctx, message_id: int):
        await ctx.message.delete()

        guild = ctx.guild
        channel = ctx.channel
        message = await channel.fetch_message(message_id)

        ctx.db.execute("INSERT INTO verification (guild_id, channel_id, message_id) VALUES (%s, %s, %s)", (guild.id, channel.id, message.id))

        await message.add_reaction(core.utils.get(self.bot.emojis, name="Verification"))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        author = guild.get_member(payload.user_id)
        channel = self.bot.get_channel(payload)

        if author.bot:
            return

        studentRole = core.utils.get(guild.roles, name="Student")
        await author.add_roles(studentRole)


def setup(bot):
    bot.add_cog(Verification(bot))
    print("Cog loaded: Verification")
