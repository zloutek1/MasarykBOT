
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Union

import inject
import discord

import bot.db



T = TypeVar('T')
R = TypeVar('R')



class Backup(ABC, Generic[T]):
    @abstractmethod
    async def traverseUp(self, obj: T) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def backup(self, obj: T) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def traverseDown(self, obj: T) -> None:
        raise NotImplementedError()
        


class GuildBackup(Backup[discord.Guild]):
    @inject.autoparams('guildRepository', 'mapper')
    def __init__(self, guildRepository: bot.db.GuildRepository, mapper: bot.db.GuildMapper) -> None:
        self.guildRepository = guildRepository
        self.mapper = mapper


    async def traverseUp(self, guild: discord.Guild) -> None:
        await self.backup(guild)


    async def backup(self, guild: discord.Guild) -> None:
        print("backup guild", guild)
        columns = await self.mapper.map(guild)
        await self.guildRepository.insert([columns])


    async def traverseDown(self, guild: discord.Guild) -> None:
        await self.backup(guild)
        
        for user in guild.members:
            await UserBackup().traverseDown(user)

        for role in guild.roles:
            await RoleBackup().traverseDown(role)

        for emoji in guild.emojis:
            await EmojiBackup().traverseDown(emoji)

        for text_channel in filter(lambda ch: ch.category is None, guild.text_channels):
            await TextChannelBackup().traverseDown(text_channel)

        for category in guild.categories:
            await CategoryBackup().traverseDown(category)



class UserBackup(Backup[discord.User | discord.Member]):
    @inject.autoparams('userRepository', 'mapper')
    def __init__(self, userRepository: bot.db.UserRepository, mapper: bot.db.UserMapper) -> None:
        self.userRepository = userRepository
        self.mapper = mapper


    async def traverseUp(self, user: discord.User | discord.Member) -> None:
        if isinstance(user, discord.Member):
            await GuildBackup().traverseUp(user.guild)
        await self.backup(user)


    async def backup(self, user: discord.User | discord.Member) -> None:
        print("backup user", user)
        columns = await self.mapper.map(user)
        await self.userRepository.insert([columns])


    async def traverseDown(self, user: discord.User | discord.Member) -> None:
        await self.backup(user)



class RoleBackup(Backup[discord.Role]):
    @inject.autoparams('roleRepository', 'mapper')
    def __init__(self, roleRepository: bot.db.RoleRepository, mapper: bot.db.RoleMapper) -> None:
        self.roleRepository = roleRepository
        self.mapper = mapper


    async def traverseUp(self, role: discord.Role) -> None:
        await GuildBackup().traverseUp(role.guild)
        await self.backup(role)


    async def backup(self, role: discord.Role) -> None:
        print("backup role", role)
        columns = await self.mapper.map(role)
        await self.roleRepository.insert([columns])


    async def traverseDown(self, role: discord.Role) -> None:
        await self.backup(role)



class EmojiBackup(Backup[discord.Emoji | discord.PartialEmoji | str]):
    @inject.autoparams('emojiRepository', 'mapper')
    def __init__(self, emojiRepository: bot.db.EmojiRepository, mapper: bot.db.EmojiMapper) -> None:
        self.emojiRepository = emojiRepository
        self.mapper = mapper


    async def traverseUp(self, emoji: discord.Emoji | discord.PartialEmoji | str) -> None:
        if isinstance(emoji, discord.Emoji) and emoji.guild:
            await GuildBackup().traverseUp(emoji.guild)
        await self.backup(emoji)


    async def backup(self, emoji: discord.Emoji | discord.PartialEmoji | str) -> None:
        print("backup emoji", emoji)
        columns = await self.mapper.map(emoji)
        await self.emojiRepository.insert([columns])


    async def traverseDown(self, emoji: discord.Emoji | discord.PartialEmoji | str) -> None:
        await self.backup(emoji)



class CategoryBackup(Backup[discord.CategoryChannel]):
    @inject.autoparams('categoryDao', 'mapper')
    def __init__(self, categoryDao: bot.db.CategoryRepository, mapper: bot.db.CategoryMapper) -> None:
        self.categoryDao = categoryDao
        self.mapper = mapper


    async def traverseUp(self, category: discord.CategoryChannel) -> None:
        await GuildBackup().traverseUp(category.guild)
        await self.backup(category)


    async def backup(self, category: discord.CategoryChannel) -> None:
        print("backup category", category)
        columns = await self.mapper.map(category)
        await self.categoryDao.insert([columns])


    async def traverseDown(self, category: discord.CategoryChannel) -> None:
        await self.backup(category)
        
        for text_channel in category.text_channels:
            await TextChannelBackup().traverseDown(text_channel)



class TextChannelBackup(Backup[discord.TextChannel]):
    @inject.autoparams('channelRepository', 'mapper')
    def __init__(self, channelRepository: bot.db.ChannelRepository, mapper: bot.db.ChannelMapper) -> None:
        self.channelRepository = channelRepository
        self.mapper = mapper


    async def traverseUp(self, text_channel: discord.TextChannel) -> None:
        if isinstance(text_channel, discord.abc.GuildChannel):
            if text_channel.category:
                await CategoryBackup().traverseUp(text_channel.category)
            else:
                await GuildBackup().traverseUp(text_channel.guild)

        await self.backup(text_channel)


    async def backup(self, text_channel: discord.TextChannel) -> None:
        print("backup text channel", text_channel)
        columns = await self.mapper.map(text_channel)
        await self.channelRepository.insert([columns])


    async def traverseDown(self, text_channel: discord.TextChannel) -> None:
        await self.backup(text_channel)

        async for message in text_channel.history():
            await MessageBackup().traverseDown(message)



class MessageBackup(Backup[discord.Message]):
    @inject.autoparams('messageRepository', 'mapper')
    def __init__(self, messageRepository: bot.db.MessageRepository, mapper: bot.db.MessageMapper) -> None:
        self.messageRepository = messageRepository
        self.mapper = mapper


    async def traverseUp(self, message: discord.Message) -> None:
        await TextChannelBackup().traverseUp(message.channel)
        await self.backup(message)


    async def backup(self, message: discord.Message) -> None:
        print("backup message", message)
        columns = await self.mapper.map(message)
        await self.messageRepository.insert([columns])


    async def traverseDown(self, message: discord.Message) -> None:
        await self.backup(message)

        for reaction in message.reactions:
            await ReactionBackup().traverseDown(reaction)

        for attachment in message.attachments:
            await AttachmentBackup(message.id).traverseDown(attachment)



class ReactionBackup(Backup[discord.Reaction]):
    @inject.autoparams('reactionRepository', 'mapper')
    def __init__(self, reactionRepository: bot.db.ReactionRepository, mapper: bot.db.ReactionMapper) -> None:
        self.reactionRepository = reactionRepository
        self.mapper = mapper


    async def traverseUp(self, reaction: discord.Reaction) -> None:
        await EmojiBackup().traverseUp(reaction.emoji)
        await MessageBackup().traverseUp(reaction.message)
        await self.backup(reaction)


    async def backup(self, reaction: discord.Reaction) -> None:
        print("backup reaction", reaction)
        columns = await self.mapper.map(reaction)
        await self.reactionRepository.insert([columns])


    async def traverseDown(self, reaction: discord.Reaction) -> None:
        await self.backup(reaction)



class AttachmentBackup(Backup[discord.Attachment]):
    @inject.autoparams('attachmentRepository', 'mapper')
    def __init__(self, message_id: int | None, attachmentRepository: bot.db.AttachmentRepository, mapper: bot.db.AttachmentMapper) -> None:
        self.message_id = message_id
        self.attachmentRepository = attachmentRepository
        self.mapper = mapper


    async def traverseUp(self, attachment: discord.Attachment) -> None:
        await self.backup(attachment)


    async def backup(self, attachment: discord.Attachment) -> None:
        print("backup attachment", attachment)
        columns = await self.mapper.map(attachment)

        tmp = list(columns)
        tmp[0] = self.message_id
        columns = tuple(tmp) # type: ignore[assignment]

        await self.attachmentRepository.insert([columns])


    async def traverseDown(self, attachment: discord.Attachment) -> None:
        await self.backup(attachment)



"""
T = TypeVar('T')
C = TypeVar('C')

log = logging.getLogger(__name__)



class Collectable(Generic[T, C]):
    def __init__(
        self,
        prepare_fn: Callable[[T], Awaitable[List[C]]],
        insert_fn: Callable[..., Awaitable[None]]
    ) -> None:
        self.content: List[C] = []
        self.prepare_fn = prepare_fn
        self.insert_fn = insert_fn


    async def add(self, item: T) -> None:
        self.content.extend(await self.prepare_fn(item))


    async def db_insert(self) -> None:
        for batch in chunks(self.content, 550):
            await self.insert_fn(batch)


    def __repr__(self) -> str:
        return f"<Collectable prepare_fn={self.prepare_fn.__qualname__} insert_fn={self.insert_fn.__qualname__}>"



class GetCollectables:
    attachmentDao = inject.attr(AttachmentDao)
    emojiDao = inject.attr(EmojiDao)
    reactionDao = inject.attr(ReactionDao)
    messageEmojiDao = inject.attr(MessageEmojiDao)

    @classmethod
    def get_collectables(cls) -> List[Collectable]:
        return [
            Collectable(
                prepare_fn=cls.attachmentDao.prepare_from_message,
                insert_fn=cls.attachmentDao.insert
            ),
            Collectable(
                prepare_fn=cls.emojiDao.prepare_from_message,
                insert_fn=cls.emojiDao.insert
            ),
            Collectable(
                prepare_fn=cls.reactionDao.prepare_from_message,
                insert_fn=cls.reactionDao.insert
            ),
            Collectable(
                prepare_fn=cls.messageEmojiDao.prepare_from_message,
                insert_fn=cls.messageEmojiDao.insert
            )
        ]

class BackupInProgressException(Exception):
    pass

class BackupUntilPresent(GetCollectables):
    guildRepository = guildRepository()
    categoryDao = CategoryDao()
    roleDao = RoleDao()
    userRepository = userRepository()
    channelRepository = channelRepository()
    messageRepository = messageRepository()
    emojiDao = EmojiDao()
    reactionDao = ReactionDao()

    loggerDao = LoggerDao()

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.backup_in_progress = False

    async def backup(self) -> None:
        if self.backup_in_progress:
           raise BackupInProgressException

        self.backup_in_progress = True
        try:
            await self._start_backup()
        finally:
            self.backup_in_progress = False

    async def _start_backup(self) -> None:
        log.info("Starting backup process")
        await self.backup_guilds(self.bot.guilds)

        for guild in self.bot.guilds:
            log.info("Backing up everything in guild: %s", guild)
            await self.backup_categories(guild.categories)
            await self.backup_roles(guild.roles)
            await self.backup_members(guild.members)
            await self.backup_channels(guild.text_channels)

            for channel in guild.text_channels:
                changed = await self.backup_messages(channel)
                if changed:
                    await asyncio.sleep(5)

        log.info("Finished backup process")

    async def backup_guilds(self, guilds: List[Guild]) -> None:
        log.info(f"backing up {len(guilds)} guilds")
        data = await self.guildRepository.prepare(guilds)
        await self.guildRepository.insert(data)

    async def backup_categories(self, categories: List[CategoryChannel]) -> None:
        log.info(f"backing up {len(categories)} categories")
        data = await self.categoryDao.prepare(categories)
        await self.categoryDao.insert(data)

    async def backup_roles(self, roles: List[Role]) -> None:
        log.info(f"backing up {len(roles)} roles")
        data = await self.roleDao.prepare(roles)
        await self.roleDao.insert(data)

    async def backup_members(self, members: List[Member]) -> None:
        log.info(f"backing up {len(members)} members")
        for chunk in chunks(members, 550):
            data = await self.userRepository.prepare(chunk)
            await self.userRepository.insert(data)

    async def backup_channels(self, text_channels: List[TextChannel]) -> None:
        log.info(f"backing up {len(text_channels)} channels")
        data = await self.channelRepository.prepare(text_channels)
        await self.channelRepository.insert(data)

    async def backup_messages(self, channel: TextChannel) -> bool:
        past = {record.get('channel_id'): record.get('id')
                for record in await self.loggerDao.select_latest_backup_message_ids()}

        if channel.last_message_id is None:
            log.info("skipping messages in empty channel %s (%s)", channel, channel.guild)
            return False

        if channel.last_message_id == past.get(channel.id):
            log.info("skipping messages in caught up channel %s (%s)", channel, channel.guild)
            return False

        log.info("backing up messages in (%s, %s)", channel, channel.guild)

        await self.backup_failed_weeks(channel)
        return await self.backup_new_weeks(channel)

    async def backup_failed_weeks(self, channel: TextChannel) -> bool:
        changed = False
        while _still_failed := await self.backup_failed_week(channel):
            log.debug("finished running failed process, re-checking if everything is fine...")
            changed = True
            await asyncio.sleep(3)
        return changed

    async def backup_failed_week(self, channel: TextChannel) -> bool:
        rows = await self.loggerDao.select(channel.id)
        failed_rows = [row for row in rows if row["finished_at"] is None]

        for failed_row in failed_rows:
            await self.try_to_backup_in_range(channel, failed_row["from_date"], failed_row["to_date"])

        return len(failed_rows) != 0

    async def backup_new_weeks(self, channel: TextChannel) -> bool:
        changed = False
        while _still_behind := await self.backup_new_week(channel):
            log.debug("newer week exists, re-running backup for next week")
            changed = True
            await asyncio.sleep(2)
        return changed

    async def backup_new_week(self, channel: TextChannel) -> bool:
        finished_process = await self.get_latest_finished_process(channel)
        (from_date, to_date) = self.get_next_week(channel, finished_process)

        await self.try_to_backup_in_range(channel, from_date, to_date, is_first_week=finished_process is None)

        return to_date < datetime.now()

    async def get_latest_finished_process(self, channel: TextChannel) -> Optional[Record]:
        finished_processes = await self.loggerDao.select(channel.id)
        if not finished_processes:
            return None

        def compare(proc: Record) -> Tuple[datetime, datetime]:
            # sort by highest finish date, then by to_date
            return (proc["finished_at"] or datetime.min, proc["to_date"])

        return max(finished_processes, key=compare)

    @staticmethod
    def get_next_week(channel: TextChannel, process: Optional[Record]) -> Tuple[datetime, datetime]:
        if process is None:
            from_date, to_date = channel.created_at, channel.created_at + timedelta(weeks=1)
        else:
            from_date, to_date = process["to_date"], process["to_date"] + timedelta(weeks=1)

        from_date, to_date = from_date.replace(tzinfo=None), to_date.replace(tzinfo=None)

        now = datetime.now()
        if from_date > now:
            from_date, to_date = now - timedelta(days=1), now + timedelta(weeks=1)

        return from_date, to_date


    async def try_to_backup_in_range(self, channel: TextChannel, from_date: datetime, to_date: datetime, is_first_week: bool = False) -> None:
        try:
            await self.backup_in_range(channel, from_date, to_date, is_first_week)
        except Forbidden:
            log.debug("missing permissions to backup messages in %s (%s)", channel, channel.guild)
        except NotFound:
            log.debug("channel %s was not found in (%s)", channel, channel.guild)
        except asyncio.TimeoutError:
            log.warn("backup in %s between %s-%s timed out", channel, from_date, to_date)

    async def backup_in_range(self, channel: TextChannel, from_date: datetime, to_date: datetime, is_first_week: bool) -> None:
        async with self.loggerDao.process(channel.id, from_date, to_date, is_first_week):
            log.info("backing up messages {%s} - {%s} in %s (%s)", from_date.strftime('%d.%m.%Y'), to_date.strftime('%d.%m.%Y'), channel, channel.guild)

            members = []
            messages = []
            collectables = self.get_collectables()
            async for message in channel.history(after=from_date, before=to_date, limit=1_000_000, oldest_first=True):
                members.append(await self.userRepository.prepare_one(message.author))
                messages.append(await self.messageRepository.prepare_one(message))
                for collectable in collectables:
                    await collectable.add(message)

            else:
                for user_batch in chunks(members, 550):
                    await self.userRepository.insert(user_batch)

                for msg_batch in chunks(messages, 550):
                    await self.messageRepository.insert(msg_batch)

                for collectable in collectables:
                    await collectable.db_insert()


class BackupOnEvents(GetCollectables):
    guildRepository = guildRepository()
    categoryDao = CategoryDao()
    roleDao = RoleDao()
    userRepository = userRepository()
    channelRepository = channelRepository()
    messageRepository = messageRepository()

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        self.insert_queues: Dict[Callable[..., Awaitable[None]], deque[Tuple]] = defaultdict(deque)
        self.update_queues: Dict[Callable[..., Awaitable[None]], deque[Tuple]] = defaultdict(deque)
        self.delete_queues: Dict[Callable[..., Awaitable[None]], deque[Tuple]] = defaultdict(deque)

        self.task_put_queues_to_database.start()

    def cog_unload(self) -> None:
        self.task_put_queues_to_database.cancel()

    ###
    #
    # Guild
    #
    ###

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild) -> None:
        log.info("joined guild %s", guild)
        data = await self.guildRepository.prepare_one(guild)
        self.insert_queues[self.guildRepository.insert].append(data)

    @commands.Cog.listener()
    async def on_guild_update(self, before: Guild, after: Guild) -> None:
        log.info("updated guild from %s to %s", before, after)
        data = await self.guildRepository.prepare_one(after)
        self.update_queues[self.guildRepository.update].append(data)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild) -> None:
        log.info("left guild %s", guild)
        data = (guild.id,)
        self.delete_queues[self.guildRepository.soft_delete].append(data)

    ###
    #
    # Channel
    #
    ###

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: GuildChannel) -> None:
        log.info("created channel %s (%s)", channel, channel.guild)

        if isinstance(channel, TextChannel):
            await self.on_textchannel_create(channel)

        elif isinstance(channel, CategoryChannel):
            await self.on_category_create(channel)

    async def on_textchannel_create(self, channel: TextChannel) -> None:
        data = await self.channelRepository.prepare_one(channel)
        self.insert_queues[self.channelRepository.insert].append(data)

    async def on_category_create(self, channel: CategoryChannel) -> None:
        data = await self.categoryDao.prepare_one(channel)
        self.insert_queues[self.categoryDao.insert].append(data)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: GuildChannel, after: GuildChannel) -> None:
        log.info("updated channel %s (%s)", before, before.guild)

        if isinstance(before, TextChannel) and isinstance(after, TextChannel):
            await self.on_textchannel_update(before, after)

        elif isinstance(before, CategoryChannel) and isinstance(after, CategoryChannel):
            await self.on_category_update(before, after)

    async def on_textchannel_update(self, _before: TextChannel, after: TextChannel) -> None:
        data = await self.channelRepository.prepare_one(after)
        self.update_queues[self.channelRepository.update].append(data)

    async def on_category_update(self, _before: CategoryChannel, after: CategoryChannel) -> None:
        data = await self.categoryDao.prepare_one(after)
        self.update_queues[self.categoryDao.update].append(data)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: GuildChannel) -> None:
        log.info("deleted channel %s (%s)", channel, channel.guild)

        if isinstance(channel, TextChannel):
            await self.on_textchannel_delete(channel)

        elif isinstance(channel, CategoryChannel):
            await self.on_category_delete(channel)

    async def on_textchannel_delete(self, channel: TextChannel) -> None:
        data = (channel.id,)
        self.delete_queues[self.channelRepository.soft_delete].append(data)

    async def on_category_delete(self, channel: CategoryChannel) -> None:
        data = (channel.id,)
        self.delete_queues[self.categoryDao.soft_delete].append(data)


    ###
    #
    # Message
    #
    ###

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        if isinstance(message.channel, PrivateChannel):
            return

        if not isinstance(message.author, Member):
            return

        msg_data = await self.messageRepository.prepare_one(message)
        self.insert_queues[self.messageRepository.insert].append(msg_data)

        colleactables = self.get_collectables()
        for collectable in colleactables:
            data = await collectable.prepare_fn(message)
            self.insert_queues[collectable.insert_fn].extend(data)

    @commands.Cog.listener()
    async def on_message_edit(self, before: Message, after: Message) -> None:
        if isinstance(before.channel, PrivateChannel):
            return

        msg_data = await self.messageRepository.prepare_one(after)
        self.update_queues[self.messageRepository.update].append(msg_data)

        colleactables = self.get_collectables()
        for collectable in colleactables:
            data = await collectable.prepare_fn(after)
            self.update_queues[collectable.insert_fn].extend(data)

    @commands.Cog.listener()
    async def on_message_delete(self, message: Message) -> None:
        if isinstance(message.channel, PrivateChannel):
            return

        data = (message.id,)
        self.delete_queues[self.messageRepository.soft_delete].append(data)

    ###
    #
    # Reaction
    #
    ###

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user: Member) -> None:
        msg_data = await self.messageRepository.prepare_one(reaction.message)
        self.insert_queues[self.messageRepository.insert].append(msg_data)

        user_data = await self.userRepository.prepare_one(user)
        self.insert_queues[self.userRepository.insert].append(user_data)

        emoji_data = await self.emojiDao.map_one(reaction.emoji)
        self.insert_queues[self.emojiDao.insert].append(emoji_data)

        react_data = await self.reactionDao.map_one(reaction)
        self.insert_queues[self.reactionDao.insert].append(react_data)

    ###
    #
    # Member
    #
    ###

    @commands.Cog.listener()
    async def on_member_join(self, member: Member) -> None:
        log.info("member %s joined (%s)", member, member.guild)

        data = await self.userRepository.prepare_one(member)
        self.insert_queues[self.userRepository.insert].append(data)

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member) -> None:
        if before.avatar != after.avatar:
            log.info("member %s updated his avatar_url (%s)", before, before.guild)
        elif before.name != after.name:
            log.info("member %s (%s) updated his name to %s (%s)", before, before.nick, after, before.guild)
        elif before.nick != after.nick:
            log.info("member %s (%s) updated his nickname to %s (%s)", before, before.nick, after.nick, before.guild)
        else:
            return

        data = await self.userRepository.prepare_one(after)
        self.update_queues[self.userRepository.update].append(data)

    @commands.Cog.listener()
    async def on_member_remove(self, member: Member) -> None:
        log.info("member %s left (%s)", member, member.guild)

        data = (member.id,)
        await self.userRepository.soft_delete([])
        self.delete_queues[self.userRepository.soft_delete].append(data)

    ###
    #
    # Role
    #
    ###

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: Role) -> None:
        log.info("added role %s (%s)", role, role.guild)

        data = await self.roleDao.prepare_one(role)
        self.insert_queues[self.roleDao.insert].append(data)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: Role, after: Role) -> None:
        log.info("updated role from %s to %s (%s)", before, after, before.guild)

        data = await self.roleDao.prepare_one(after)
        self.update_queues[self.roleDao.update].append(data)

    @commands.Cog.listener()
    async def on_guild_role_remove(self, role: Role) -> None:
        log.info("removed role %s (%s)", role, role.guild)

        data = (role.id,)
        self.delete_queues[self.roleDao.soft_delete].append(data)

    ###
    #
    # Loop
    #
    ###

    @tasks.loop(minutes=5)
    async def task_put_queues_to_database(self) -> None:
        def total(queue: Dict[Callable, deque[Tuple]]) -> int:
            return sum(len(v) for v in queue.values())

        async def do() -> None:
            log.info("putting queues to database (ins %s, upd %s, del %s)", inserts, updates, deletes)
            await self.put_queues_to_database(self.insert_queues, limit=2_000)
            await self.put_queues_to_database(self.update_queues, limit=1_000)
            await self.put_queues_to_database(self.delete_queues, limit=1_000)

        inserts = total(self.insert_queues)
        updates = total(self.update_queues)
        deletes = total(self.delete_queues)

        if inserts == 0 and updates == 0 and deletes == 0:
            return

        await do()
        while (inserts > 2_000 or updates > 1_000 or deletes > 1_000):
            await do()
            await asyncio.sleep(5)

            inserts = total(self.insert_queues)
            updates = total(self.update_queues)
            deletes = total(self.delete_queues)

    async def put_queues_to_database(
        self,
        queues: Dict[Callable[[List[Tuple]], Awaitable[None]], deque[Tuple]],
        *,
        limit: int = 1000
    ) -> None:
        for (put_fn, queue) in queues.items():
            await self.put_queue_to_database(put_fn, queue, limit=limit)

    async def put_queue_to_database(
        self,
        put_fn: Callable[[List[Tuple]], Awaitable[None]],
        queue: deque[Tuple],
        *,
        limit: int = 1000
    ) -> None:
        if len(queue) == 0:
            return

        take_elements = min(limit, len(queue))
        elements = [queue.popleft() for _ in range(take_elements)]
        log.debug("Putting %s from queue to database (%s)", len(elements), put_fn.__qualname__)

        await put_fn(elements)

class Logger(commands.Cog, BackupUntilPresent, BackupOnEvents):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        BackupUntilPresent.__init__(self, bot)
        BackupOnEvents.__init__(self, bot)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.backup()

    @tasks.loop(hours=168)  # 168 hours == 1 week
    async def _repeat_backup(self) -> None:
        await self.backup()

    @commands.command(name="backup")
    @commands.has_permissions(administrator=True)
    async def _backup(self, ctx: Context) -> None:
        if self.backup_in_progress:
            await ctx.send_error("Backup is already running")
            return

        await self.backup()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Logger(bot))
"""