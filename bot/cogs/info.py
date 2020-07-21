from discord import Embed, Color
from discord.ext import commands
from discord.utils import get

import time
from datetime import datetime


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def uptime(self, ctx):
        running_for = datetime.now() - self.bot.uptime
        await ctx.send_embed(f"I have been running for {running_for}")

    @commands.command()
    async def ping(self, ctx):
        """Feeling lonely?"""
        before_typing = time.monotonic()
        await ctx.trigger_typing()
        after_typing = time.monotonic()
        ms = int((after_typing - before_typing) * 1000)
        msg = ':ping_pong: **PONG!** (~{}ms)'.format(ms)
        await ctx.channel.send(msg)

    @commands.command()
    async def info(self, ctx):
        """
        send an embed containing info in format
        Server_id           Owner

        Channels
        text | category | voice
        Total:

        Members
        online | idle | dnd | streaming | offline
        Total:
        """

        status = {}
        for member in ctx.guild.members:
            status[member.status.name] = status.get(member.status.name, 0) + 1

        online = get(self.bot.emojis, name="status_online")
        idle = get(self.bot.emojis, name="status_idle")
        dnd = get(self.bot.emojis, name="status_dnd")
        streaming = get(self.bot.emojis, name="status_streaming")
        offline = get(self.bot.emojis, name="status_offline")

        category = get(self.bot.emojis, name="category_channel")
        text = get(self.bot.emojis, name="text_channel")
        voice = get(self.bot.emojis, name="voice_channel")

        embed = Embed(
            title=f"{ctx.guild.name}",
            description=f"{ctx.guild.description if ctx.guild.description else ''}",
            color=Color.from_rgb(0, 0, 0))
        embed.add_field(
            name="ID",
            value=(f"{ctx.guild.id}")
        )
        embed.add_field(
            name="Owner",
            value=(f"{ctx.guild.owner}")
        )
        embed.add_field(
            name="Channels",
            value=("{text} {text_count} " +
                   "{category} {category_count} " +
                   "{voice} {voice_count}").format(
                 text=text, text_count=len(ctx.guild.text_channels),
                 category=category, category_count=len(ctx.guild.categories),
                 voice=voice, voice_count=len(ctx.guild.voice_channels)
            ) + f"\n**Total:** {len(ctx.guild.channels)}",
            inline=False
        )
        embed.add_field(
            name="Members",
            value=("{online} {online_count} " +
                   "{idle} {idle_count} " +
                   "{dnd} {dnd_count} " +
                   "{streaming} {streaming_count} " +
                   "{offline} {offline_count}").format(
                online=online, online_count=status.get("online", 0),
                idle=idle, idle_count=status.get("idle", 0),
                dnd=dnd, dnd_count=status.get("dnd", 0),
                streaming=streaming, streaming_count=status.get(
                    "streaming", 0),
                offline=offline, offline_count=status.get("offline", 0)) +
            f"\n**Total:** {len(ctx.guild.members)}",
            inline=False
        )

        author = ctx.message.author
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        embed.set_footer(text=f"{str(author)} at {time_now}", icon_url=author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Info(bot))
