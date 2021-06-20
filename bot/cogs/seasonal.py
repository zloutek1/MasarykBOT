from os import stat
from typing import Optional
from discord.ext import tasks, commands
from datetime import datetime
from contextlib import suppress

from discord.ext.commands.core import has_permissions


class Seasonal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        self.check_season.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_season.start()

    @tasks.loop(hours=6)
    async def check_season(self):
        """
        check for any seasons matching current time and update
        discord display according to that season
        """

        for guild in self.bot.guilds:
            await self.check_season_in_guild(guild)

    async def check_season_in_guild(self, guild):
        if (current_event := await self.bot.db.seasons.load_current_event(guild.id)) is None:
            if (current_event := await self.bot.db.seasons.load_default_event(guild.id)) is None:
                return

        if current_event["icon"] is not None:
            await guild.edit(icon=current_event['icon'], reason="Switching to seasonal event " + current_event['event_name'])

        if current_event["banner"] is not None:
            await guild.edit(banner=current_event['banner'], reason="Switching to seasonal event " + current_event['event_name'])

    @commands.group(aliases=['season'])
    async def seasonal(self, ctx):
        pass

    @seasonal.command(name='current')
    async def current_event(self, ctx):
        """
        Display current seasonal event
        """
        if (current_event := await self.bot.db.seasons.load_current_event(ctx.guild.id)) is None:
            return await ctx.send_embed("There are no seasonal event", name="seasonal events")
        await ctx.send_embed(f"Current event is {current_event['event_name']}", name="seasonal events")

    @seasonal.command(name='events', aliases=['all', 'list'])
    async def all_events(self, ctx):
        """
        Display all seasonal events
        """
        def format(event):
            dates = (f"*{event['from_date'].strftime('%d.%m.%Y')}-{event['to_date'].strftime('%d.%m.%Y')}*"
                     if event['from_date'] is not None and event['to_date'] is not None else
                     "")
            return f"» {dates: >19} {event['event_name']}"

        def right_justify(text, by=0, pad=" "):
            return pad * (by - len(str(text))) + str(text)

        events = await self.bot.db.seasons.load_events(ctx.guild.id)
        formatted_events = "\n".join(map(format, events))
        await ctx.send_embed(formatted_events or "There are no events for this guild", name=f"Upcomming seasonal events: \n")

    @seasonal.command(name='add')
    @has_permissions(administrator=True)
    async def add_event(self, ctx, name: str, from_date: str, to_date: str):
        """
        Add a new seasonal event
        example: !seasonal add myname 15.08.2020T00:00 11.6.2022T00:00

        Add the default event with
        example: !seasonal add default None None
        """

        from_date = self.parse_time(from_date)
        to_date = self.parse_time(to_date)

        if to_date < from_date:
            await ctx.send("invalid date ranges")
            return

        icon = await self.prompt_icon(ctx)
        banner = await self.prompt_banner(ctx)

        event = (ctx.guild.id, name, from_date, to_date, icon, banner)
        await self.bot.db.seasons.insert([event])

        await ctx.send_embed(f"added event {name}", name=f"seasonal events")

    @staticmethod
    def parse_time(time: str) -> Optional[datetime]:
        if time is None or time.lower() == 'none':
            return None
        with suppress(ValueError):
            return datetime.strptime(time, '%d.%m.%YT%H:%M')
        with suppress(ValueError):
            return datetime.strptime(time, '%d.%m.%Y')

    async def prompt_icon(self, ctx):
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        await ctx.send_embed("Please send new logo (write None for empty)", name=f"seasonal events")
        icon_msg = await self.bot.wait_for('message', check=check, timeout=120.0)

        icon = None
        if icon_msg.attachments and icon_msg.content.lower() != "none":
            icon = await icon_msg.attachments[0].read()

        return icon

    async def prompt_banner(self, ctx):
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        await ctx.send_embed("Please send new banner (write None for empty)", name=f"seasonal events")
        banner_msg = await self.bot.wait_for('message', check=check, timeout=120.0)

        banner = None
        if banner_msg.attachments and banner_msg.content.lower() != "none":
            banner = await banner_msg.attachments[0].read()

        return banner

    @seasonal.command()
    @has_permissions(administrator=True)
    async def remove(self, ctx, name: str):
        await self.bot.db.seasons.delete(ctx.guild.id, name)
        await ctx.send_embed(f"removed event {name}", name=f"seasonal events")

    @seasonal.command()
    @has_permissions(administrator=True)
    async def sync(self, ctx):
        await self.check_season_in_guild(ctx.guild)

def setup(bot):
    bot.add_cog(Seasonal(bot))
