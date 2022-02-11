import asyncio
import itertools
from contextlib import suppress
from datetime import datetime, timedelta, timezone

from disnake import Embed
from disnake.ext import commands, tasks
from disnake.ext.commands.core import has_permissions


class SeasonDate(commands.Converter):
    async def convert(self, ctx, argument):
        with suppress(ValueError):
            return datetime.strptime(argument, '%d.%m.%YT%H:%M')
        with suppress(ValueError):
            return datetime.strptime(argument, '%d.%m.%Y')
        raise commands.BadArgument(f"Failed to parse datetime {argument}")


CEST = timezone(offset=timedelta(hours=+2))
def next_midnight(timezone):
    return datetime.now(timezone)\
                   .replace(hour=0, minute=0, second=0, microsecond=0) \
                   + timedelta(days=1)


def partition(items, predicate=bool):
    a, b = itertools.tee((predicate(item), item) for item in items)
    return ((item for pred, item in a if not pred),
            (item for pred, item in b if pred))



class Seasonal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        self.check_season.cancel()



    @commands.group(aliases=['seasonal', 'seasons'])
    async def season(self, ctx):
        pass

    @season.command()
    async def current(self, ctx):
        if (current_event := await self.bot.db.seasons.load_current_event(ctx.guild.id)) is None:
            return await ctx.send_embed("There are no seasonal event", name="seasonal events")
        await ctx.send_embed(f"Current event is {current_event['name']} (**{current_event['id']}**)", name="seasonal events")

    @season.command(name="list", aliases=['all'])
    async def list_all(self, ctx):
        def format(event):
            dates = (f"*{event['from_date'].strftime('%d.%m.%Y')}-{event['to_date'].strftime('%d.%m.%Y')}*"
                     if event['from_date'] is not None and event['to_date'] is not None else
                     "")
            return f"» {dates: >19} (**{event['id']}**) \n​ ​ ​ ​ {event['name']}\n"

        events = await self.bot.db.seasons.load_events(ctx.guild.id)
        (past_events, upcoming_events) = partition(events, lambda e: e['to_date'] > datetime.now(CEST))

        if not events:
            await ctx.send("There are no events for this guild")
            return

        embed = Embed()
        embed.add_field(name="Upcoming events: \n", value="\n".join(list(map(format, upcoming_events))) or "No upcoming events")
        embed.add_field(name="Past events: \n", value="\n".join(list(map(format, past_events))[-5:][::-1]) or "No past events")

        await ctx.send(embed=embed)


    @season.command(name="add")
    @has_permissions(administrator=True)
    async def add_season(self, ctx, name,
                               from_date: SeasonDate, to_date: SeasonDate,
                               should_change_icon = True, should_change_banner = False):
        if to_date <= from_date:
            await ctx.send("invalid date range")
            return

        if name == "default":
            await ctx.send("this name is not allowed")
            return

        icon = await self.prompt_icon(ctx) if should_change_icon else None
        banner = await self.prompt_icon(ctx) if should_change_banner else None

        event = (ctx.guild.id, name, from_date, to_date, icon, banner)
        await self.bot.db.seasons.insert([event])

        await ctx.send_embed(f"added event {name}", name=f"seasonal events")


    @season.group(name="set")
    @has_permissions(administrator=True)
    async def season_set(self, ctx):
        pass

    @season_set.command(name="default")
    async def set_default_season(self, ctx, should_change_icon = True, should_change_banner = False):
        icon = await self.prompt_icon(ctx) if should_change_icon else None
        banner = await self.prompt_icon(ctx) if should_change_banner else None

        event = (ctx.guild.id, "default", None, None, icon, banner)
        await self.bot.db.seasons.insert([event])

        await ctx.send_embed(f"set default event", name=f"seasonal events")

    @season_set.command(name="icon")
    async def set_season_icon(self, ctx, id: int):
        icon = await self.prompt_icon(ctx)
        event = await self.bot.db.seasons.find(ctx.guild.id, id)
        await self.bot.db.seasons.update(ctx.guild.id, icon, event['banner'])
        await ctx.send_embed(f"Updated event with id {id}", name=f"seasonal events")

    @season_set.command(name="banner")
    async def set_season_banner(self, ctx, id: int):
        banner = await self.prompt_icon(ctx)
        event = await self.bot.db.seasons.find(ctx.guild.id, id)
        await self.bot.db.seasons.update(ctx.guild.id, event['icon'], banner)
        await ctx.send_embed(f"Updated event with id {id}", name=f"seasonal events")

    @season.command(name="remove")
    @has_permissions(administrator=True)
    async def remove_season(self, ctx, id: int):
        await self.bot.db.seasons.delete(ctx.guild.id, id)
        await ctx.send_embed(f"deleted event with id {id}", name=f"seasonal events")

    @season.command()
    @has_permissions(administrator=True)
    async def sync(self, ctx):
        await self.check_season_in_guild(ctx.guild)

    @commands.Cog.listener()
    async def on_ready(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.start_check_at_midnight())

    async def start_check_at_midnight(self):
        sleep_for = (next_midnight(CEST) - datetime.now(CEST)).total_seconds()
        await asyncio.sleep(sleep_for)

        self.check_season.start()

    @tasks.loop(hours=6)
    async def check_season(self):
        for guild in self.bot.guilds:
            await self.check_season_in_guild(guild)

    async def check_season_in_guild(self, guild):
        if (current_event := await self.bot.db.seasons.load_current_event(guild.id)) is None:
            if (current_event := await self.bot.db.seasons.load_default_event(guild.id)) is None:
                return

        if current_event["icon"] is not None:
            await guild.edit(icon=current_event['icon'], reason="Switching to seasonal event " + current_event['name'])

        if current_event["banner"] is not None:
            await guild.edit(banner=current_event['banner'], reason="Switching to seasonal event " + current_event['name'])



    async def prompt_icon(self, ctx):
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        await ctx.send_embed("Please send new logo (write None for empty)", name=f"seasonal events")
        icon_msg = await self.bot.wait_for('message', check=check, timeout=120.0)

        icon = None
        if icon_msg.attachments and icon_msg.content.lower() != "none":
            icon = await icon_msg.attachments[0].read()

        return icon

def setup(bot):
    bot.add_cog(Seasonal(bot))
