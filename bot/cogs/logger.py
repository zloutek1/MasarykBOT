import asyncio
import logging
from collections import deque, defaultdict
from datetime import datetime, timedelta

from bot.bot import MasarykBOT
from bot.cogs.utils.context import Context
from bot.cogs.utils.db import Record
from typing import List, Dict, Tuple, Optional, Callable, Generic, TypeVar, Awaitable

from discord import Guild, Role, Member, TextChannel, CategoryChannel
from discord.abc import PrivateChannel
from discord.ext import tasks, commands
from discord.ext.commands import has_permissions
from discord.errors import Forbidden, NotFound

T = TypeVar('T')

log = logging.getLogger(__name__)

def partition(cond, lst):
    return [[i for i in lst if cond(i)], [i for i in lst if not cond(i)]]

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

class GetCollectables:
    @staticmethod
    def get_collectables(bot):
        return [
            Collectable(
                prepare_fn=bot.db.members.prepare_from_message,
                insert_fn=bot.db.members.insert
            ),
            Collectable(
                prepare_fn=bot.db.attachments.prepare_from_message,
                insert_fn=bot.db.attachments.insert
            ),
            Collectable(
                prepare_fn=bot.db.reactions.prepare_from_message,
                insert_fn=bot.db.reactions.insert
            ),
            Collectable(
                prepare_fn=bot.db.emojis.prepare_from_message,
                insert_fn=bot.db.emojis.insert
            ),
            Collectable(
                prepare_fn=bot.db.message_emojis.prepare_from_message,
                insert_fn=bot.db.message_emojis.insert
            )
        ]

class BackupUntilPresent(GetCollectables):
    def __init__(self, bot: MasarykBOT):
        self.bot = bot

    async def backup(self) -> None:
        log.info("Starting backup process")
        await self.backup_guilds(self.bot.guilds)

        for guild in self.bot.guilds:
            await self.backup_categories(guild.categories)
            await self.backup_roles(guild.roles)
            await self.backup_members(guild.members)
            await self.backup_channels(guild.text_channels)

            for channel in guild.text_channels:
                await self.backup_messages(channel)

        log.info("Finished backup process")


    async def backup_guilds(self, guilds: List[Guild]) -> None:
        log.info("backing up guilds")
        data = await self.bot.db.guilds.prepare(guilds)
        await self.bot.db.guilds.insert(data)

    async def backup_categories(self, categories: List[CategoryChannel]) -> None:
        log.info("backing up categories")
        data = await self.bot.db.categories.prepare(categories)
        await self.bot.db.categories.insert(data)

    async def backup_roles(self, roles: List[Role]) -> None:
        log.info("backing up roles")
        data = await self.bot.db.roles.prepare(roles)
        await self.bot.db.roles.insert(data)

    async def backup_members(self, members: List[Member]) -> None:
        log.info("backing up members")
        for chunk in chunks(members, 550):
            data = await self.bot.db.members.prepare(chunk)
            await self.bot.db.members.insert(data)

    async def backup_channels(self, text_channels: List[TextChannel]) -> None:
        log.info("backing up channels")
        data = await self.bot.db.channels.prepare(text_channels)
        await self.bot.db.channels.insert(data)


    async def backup_messages(self, channel: TextChannel) -> None:
        log.info("backing up messages")
        await self.backup_failed_weeks(channel)
        await self.backup_new_weeks(channel)


    async def backup_failed_weeks(self, channel: TextChannel) -> None:
        while _still_failed := await self.backup_failed_week(channel):
            log.debug("finished running failed process, re-checking if everything is fine...")
            await asyncio.sleep(3)

    async def backup_failed_week(self, channel: TextChannel) -> bool:
        rows = await self.bot.db.logger.select(channel.id)
        failed_rows = [row for row in rows if row.get("finished_at") is None]

        for failed_row in failed_rows:
            await self.try_to_backup_in_range(channel, failed_row.get("from_date"), failed_row.get("to_date"))

        return len(failed_rows) != 0


    async def backup_new_weeks(self, channel: TextChannel) -> None:
        while _still_behind := await self.backup_new_week(channel):
            log.debug("newer week exists, re-running backup for next week")
            await asyncio.sleep(2)

    async def backup_new_week(self, channel: TextChannel) -> bool:
        finished_process = await self.get_latest_finished_process(channel)
        (from_date, to_date) = self.get_next_week(channel, finished_process)

        await self.try_to_backup_in_range(channel, from_date, to_date, is_first_week=finished_process is None)

        return to_date < datetime.now()

    async def get_latest_finished_process(self, channel: TextChannel) -> Record:
        finished_processes = await self.bot.db.logger.select(channel.id)
        if not finished_processes:
            return None

        def compare(proc: Record):
            # sort by highest finish date, then by to_date
            return (proc.get("finished_at") or datetime.min, proc.get("to_date"))

        return max(finished_processes, key=compare)

    @staticmethod
    def get_next_week(channel: TextChannel, process: Optional[Record]) -> Tuple[datetime, datetime]:
        if process is None:
            from_date, to_date = channel.created_at, channel.created_at + timedelta(weeks=1)
        else:
            from_date, to_date = process.get("to_date"), process.get("to_date") + timedelta(weeks=1)

        if from_date > datetime.now():
            from_date, to_date = datetime.now() - timedelta(weeks=1), datetime.now()

        return from_date, to_date


    async def try_to_backup_in_range(self, channel: TextChannel, from_date: datetime, to_date: datetime, is_first_week: bool = False) -> None:
        try:
            await self.backup_in_range(channel, from_date, to_date, is_first_week)
        except Forbidden:
            log.debug("missing permissions to backup messages in %s (%s)", channel, channel.guild)
        except NotFound:
            log.debug("channel %s was not found in (%s)", channel, channel.guild)

    async def backup_in_range(self, channel: TextChannel, from_date: datetime, to_date: datetime, is_first_week: bool) -> None:
        if channel.last_message_id is None:
            return

        log.info("backing up messages {%s} - {%s} in %s (%s)", from_date.strftime('%d.%m.%Y'), to_date.strftime('%d.%m.%Y'), channel, channel.guild)

        async with self.bot.db.logger.process(channel.id, from_date, to_date, is_first_week):
            messages = []
            collectables = self.get_collectables(self.bot)
            async for message in channel.history(after=from_date, before=to_date, limit=1_000_000, oldest_first=True):
                messages.append(await self.bot.db.messages.prepare_one(message))
                for collectable in collectables:
                    await collectable.add(message)

            else:
                for batch in chunks(messages, 550):
                    await self.bot.db.messages.insert(batch)

                for collectable in collectables:
                    await collectable.db_insert()


class BackupOnEvents(GetCollectables):
    def __init__(self, bot):
        self.bot = bot

        self.insert_queues: Dict[Callable[[List[Tuple]], Awaitable[None]], deque[Tuple]] = defaultdict(deque)
        self.update_queues: Dict[Callable[[List[Tuple]], Awaitable[None]], deque[Tuple]] = defaultdict(deque)
        self.delete_queues: Dict[Callable[[List[Tuple]], Awaitable[None]], deque[Tuple]] = defaultdict(deque)

        self.task_put_queues_to_database.start()

    def cog_unload(self):
        self.task_put_queues_to_database.cancel()

    ###
    #
    # Guild
    #
    ###

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        log.info("joined guild %s", guild)
        data = await self.bot.db.guilds.prepare_one(guild)
        self.insert_queues[self.bot.db.guilds.insert].append(data)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        log.info("updated guild from %s to %s", before, after)
        data = await self.bot.db.guilds.prepare_one(after)
        self.update_queues[self.bot.db.guilds.update].append(data)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        log.info("left guild %s", guild)
        data = (guild.id,)
        self.delete_queues[self.bot.db.guilds.soft_delete].append(data)

    ###
    #
    # Channel
    #
    ###

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        log.info("created channel %s (%s)", channel, channel.guild)

        if isinstance(channel, TextChannel):
            await self.on_textchannel_create(channel)

        elif isinstance(channel, CategoryChannel):
            await self.on_category_create(channel)

    async def on_textchannel_create(self, channel):
        data = await self.bot.db.channels.prepare_one(channel)
        self.insert_queues[self.bot.db.channels.insert].append(data)

    async def on_category_create(self, channel):
        data = await self.bot.db.categories.prepare_one(channel)
        self.insert_queues[self.bot.db.categories.insert].append(data)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        log.info("updated channel %s (%s)", before, before.guild)

        if isinstance(after, TextChannel):
            await self.on_textchannel_update(before, after)

        elif isinstance(after, CategoryChannel):
            await self.on_category_update(before, after)

    async def on_textchannel_update(self, _before, after):
        data = await self.bot.db.channels.prepare_one(after)
        self.update_queues[self.bot.db.channels.update].append(data)

    async def on_category_update(self, _before, after):
        data = await self.bot.db.categories.prepare_one(after)
        self.update_queues[self.bot.db.categories.update].append(data)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        log.info("deleted channel %s (%s)", channel, channel.guild)

        if isinstance(channel, TextChannel):
            await self.on_textchannel_delete(channel)

        elif isinstance(channel, CategoryChannel):
            await self.on_category_delete(channel)

    async def on_textchannel_delete(self, channel):
        data = (channel.id,)
        self.delete_queues[self.bot.db.channels.soft_delete].append(data)

    async def on_category_delete(self, channel):
        data = (channel.id,)
        self.delete_queues[self.bot.db.categories.soft_delete].append(data)


    ###
    #
    # Message
    #
    ###

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, PrivateChannel):
            return

        if not isinstance(message.author, Member):
            return

        data = await self.bot.db.messages.prepare_one(message)
        self.insert_queues[self.bot.db.messages.insert].append(data)

        colleactables = self.get_collectables(self.bot)
        for collectable in colleactables:
            data = await collectable.prepare_fn(message)
            self.insert_queues[collectable.insert_fn].extend(data)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if isinstance(before.channel, PrivateChannel):
            return

        data = await self.bot.db.messages.prepare_one(after)
        self.update_queues[self.bot.db.messages.update].append(data)

        colleactables = self.get_collectables(self.bot)
        for collectable in colleactables:
            data = await collectable.prepare_fn(after)
            self.update_queues[collectable.insert_fn].extend(data)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if isinstance(message.channel, PrivateChannel):
            return

        data = (message.id,)
        self.delete_queues[self.bot.db.messages.soft_delete].append(data)

    ###
    #
    # Reaction
    #
    ###

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        data = await self.bot.db.messages.prepare_one(reaction.message)
        self.insert_queues[self.bot.db.messages.insert].append(data)

        data = await self.bot.db.members.prepare_one(user)
        self.insert_queues[self.bot.db.members.insert].append(data)

        data = await self.bot.db.reactions.prepare_one(reaction)
        self.insert_queues[self.bot.db.reactions.insert].append(data)

    ###
    #
    # Member
    #
    ###

    @commands.Cog.listener()
    async def on_member_join(self, member):
        log.info("member %s joined (%s)", member, member.guild)

        data = await self.bot.db.members.prepare_one(member)
        self.insert_queues[self.bot.db.members.insert].append(data)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.avatar_url != after.avatar_url:
            log.info("member %s updated his avatar_url (%s)", before, before.guild)
        elif before.name != after.name:
            log.info("member %s (%s) updated his name to %s (%s)", before, before.nick, after, before.guild)
        elif before.nick != after.nick:
            log.info("member %s (%s) updated his nickname to %s (%s)", before, before.nick, after.nick, before.guild)
        else:
            return

        data = await self.bot.db.members.prepare_one(after)
        self.update_queues[self.bot.db.members.update].append(data)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        log.info("member %s left (%s)", member, member.guild)

        data = (member.id,)
        await self.bot.db.members.soft_delete([])
        self.delete_queues[self.bot.db.members.soft_delete].append(data)

    ###
    #
    # Role
    #
    ###

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        log.info("added role %s (%s)", role, role.guild)

        data = await self.bot.db.roles.prepare_one(role)
        self.insert_queues[self.bot.db.roles.insert].append(data)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        log.info("updated role from %s to %s (%s)", before, after, before.guild)

        data = await self.bot.db.roles.prepare_one(after)
        self.update_queues[self.bot.db.roles.update].append(data)

    @commands.Cog.listener()
    async def on_guild_role_remove(self, role):
        log.info("removed role %s (%s)", role, role.guild)

        data = (role.id,)
        self.delete_queues[self.bot.db.roles.soft_delete].append(data)

    ###
    #
    # Loop
    #
    ###

    @tasks.loop(minutes=5)
    async def task_put_queues_to_database(self):
        await self.put_queues_to_database(self.insert_queues, limit=1000)
        await self.put_queues_to_database(self.update_queues, limit=2000)
        await self.put_queues_to_database(self.delete_queues, limit=1000)

    async def put_queues_to_database(self, queues: Dict[Callable[[List[Tuple]], Awaitable[None]], deque[Tuple]], *, limit=1000):
        for (put_fn, queue) in queues.items():
            await self.put_queue_to_database(put_fn, queue, limit=limit)

    async def put_queue_to_database(self, put_fn: Callable[[List[Tuple]], Awaitable[None]], queue: deque[Tuple], *, limit=1000):
        if len(queue) == 0:
            return

        take_elements = min(limit, len(queue))
        elements = [queue.popleft() for _ in range(take_elements)]
        log.info("Putting %s from queue to database (%s)", len(elements), put_fn.__qualname__)

        await put_fn(elements)

class Collectable(Generic[T]):
    def __init__(self, prepare_fn: Callable[[T], List[Tuple]]=None, insert_fn: Callable[[List[Tuple]], None]=None):
        self.content: List[Tuple] = []
        self.prepare_fn = prepare_fn
        self.insert_fn = insert_fn

    async def add(self, item):
        self.content.extend(await self.prepare_fn(item))

    async def db_insert(self):
        for batch in chunks(self.content, 550):
            await self.insert_fn(batch)


class Logger(commands.Cog, BackupUntilPresent, BackupOnEvents):
    def __init__(self, bot: MasarykBOT):
        self.bot = bot

        BackupUntilPresent.__init__(self, bot)
        BackupOnEvents.__init__(self, bot)

    @commands.Cog.listener()
    async def on_ready(self):
        """await self.backup()"""

    @tasks.loop(hours=168)  # 168 hours == 1 week
    async def _repeat_backup(self):
        await self.backup()

    @commands.command(name="backup")
    @has_permissions(administrator=True)
    async def _backup(self, _ctx: Context):
        await self.backup()

def setup(bot):
    bot.add_cog(Logger(bot))
