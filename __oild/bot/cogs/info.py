import time
from datetime import datetime
from typing import Dict, Optional

from discord import Color, Embed
from discord.ext import commands
from discord.utils import get

from src.bot import Context, GuildContext


class InfoCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.uptime: Optional[datetime] = None

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if self.uptime is None:
            self.uptime = datetime.utcnow()

    @commands.command(name="uptime")
    async def _uptime(self, ctx: Context) -> None:
        if self.uptime is None:
            await ctx.send_embed(f"I am not running? o.O")
            return

        running_for = datetime.now() - self.uptime
        await ctx.send_embed(f"I have been running for {running_for}")

    @commands.command()
    async def ping(self, ctx: Context) -> None:
        """Feeling lonely?"""
        before_typing = time.monotonic()
        await ctx.typing()
        after_typing = time.monotonic()
        milliseconds = int((after_typing - before_typing) * 1000)
        msg = ':ping_pong: **PONG!** (~{}ms)'.format(milliseconds)
        await ctx.send(msg)

    @commands.command()
    async def invite(self, ctx: Context) -> None:
        assert self.bot.user
        await ctx.send(
            f"https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=268823632")

    @commands.command()
    @commands.guild_only()
    async def categories(self, ctx: GuildContext) -> None:
        categories = (category.name for category in ctx.guild.categories)
        await ctx.send(f"`{', '.join(categories)}`")

    @commands.command()
    @commands.guild_only()
    async def info(self, ctx: GuildContext) -> None:
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
        status: Dict[str, int] = {}
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
            name="Owner",
            value=f"{ctx.guild.owner}"
        )
        embed.add_field(
            name=f"Channels ({len(ctx.guild.channels)})",
            value=("{text} {text_count} ⁣ " +
                   "{category} {category_count} ⁣ " +
                   "{voice} {voice_count}").format(
                text=text, text_count=len(ctx.guild.text_channels),
                category=category, category_count=len(ctx.guild.categories),
                voice=voice, voice_count=len(ctx.guild.voice_channels)
            ),
            inline=False
        )
        embed.add_field(
            name=f"Members ({len(ctx.guild.members)})",
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
                offline=offline, offline_count=status.get("offline", 0)),
            inline=False
        )

        author = ctx.message.author
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        embed.set_footer(
            text=f"{str(author)} at {time_now}",
            icon_url=author.avatar.url if author.avatar else author.default_avatar.url
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(InfoCog(bot))
