import logging
from enum import auto, Enum
from typing import List, Dict, Iterable, Optional

import discord
import inject
from discord.ext import commands
from discord.utils import get

from bot.constants import CONFIG
from bot.utils import DiscordLimit
from bot.db import CourseRepository, StudentRepository, CourseEntity, StudentEntity, UnitOfWork, FacultyRepository, FacultyEntity
from bot.utils import sanitize_channel_name
from .registration_context import CourseRegistrationContext
from .trie import Trie

log = logging.getLogger(__name__)


class Status(Enum):
    REGISTERED = auto()
    SHOWN = auto()
    UNSIGNED = auto()


class CourseService:
    category_trie = Trie()

    @inject.autoparams('course_repository', 'student_repository', 'faculty_repository', 'faculty_repository', 'uow')
    def __init__(
        self,
        bot: commands.Bot,
        course_repository: CourseRepository,
        student_repository: StudentRepository,
        faculty_repository: FacultyRepository,
        uow: UnitOfWork
    ) -> None:
        self.bot = bot
        self._course_repository = course_repository
        self._student_repository = student_repository
        self._faculty_repository = faculty_repository
        self._uow = uow

    async def load_category_trie(self) -> None:
        courses = await self._course_repository.find_all_course_codes()
        self.category_trie.insert_all(courses)
        log.info(f'loaded {len(courses)} courses')

    def load_course_registration_channels(self) -> Dict[int, discord.abc.Messageable]:
        result: Dict[int, discord.TextChannel | discord.Thread] = {}
        for guild_config in CONFIG.guilds:
            if not guild_config.channels.course:
                continue
            channel_id = guild_config.channels.course.registration_channel
            if not (channel := self.bot.get_channel(channel_id)):
                continue
            if not isinstance(channel, (discord.TextChannel, discord.Thread)):
                continue
            result[channel.id] = channel
        return result

    async def autocomplete(self, pattern: str) -> List[CourseEntity]:
        return await self._course_repository.autocomplete(f'%{pattern}%')

    async def get_course_info(self, guild: discord.Guild, course: CourseEntity) -> discord.Embed:
        student_count = await self._student_repository.count_course_students((course.faculty, course.code, guild.id))

        embed = discord.Embed(
            color=CONFIG.colors.MUNI_YELLOW,
            title=f"{course.faculty}:{course.code}",
            description=f"{course.name}\n\n{course.url}"
        )
        embed.add_field(name="Students", value=student_count)
        return embed

    async def get_user_info(self, guild: discord.Guild, user: discord.Member) -> discord.Embed:
        course_codes = await self._student_repository.find_all_students_courses((guild.id, user.id))

        return discord.Embed(
            color=CONFIG.colors.MUNI_YELLOW,
            title=f"{user.display_name}'s courses",
            description=', '.join(course_codes) or "no courses registered"
        )

    async def search_courses(self, pattern: str) -> discord.Embed:
        results = await self.autocomplete(pattern)

        return discord.Embed(
            color=CONFIG.colors.MUNI_YELLOW,
            title=f'Found courses for {pattern}',
            description='\n'.join(
                f"{row.faculty}:{row.code} {row.name}"[:99]
                for row in results
            ) or 'no courses found'
        )

    async def join_course(self, guild: discord.Guild, user: discord.Member, course: CourseEntity) -> Status:
        context = CourseRegistrationContext(guild, user, course)
        await context.register_course()
        if not (channel := context.find_course_channel()):
            if not await context.should_create_course_channel():
                return Status.REGISTERED
            category = await context.create_or_get_course_category(
                self.category_trie,
                DiscordLimit.CATEGORY_MAX_CHANNELS
            )
            channel = await context.create_course_channel(category)
        await context.show_course_channel(channel)
        return Status.SHOWN

    @staticmethod
    async def leave_course(guild: discord.Guild, user: discord.Member, course: CourseEntity) -> None:
        context = CourseRegistrationContext(guild, user, course)
        await context.unregister_course()
        if channel := context.find_course_channel():
            await context.hide_course_channel(channel)

    async def leave_all_courses(self, guild: discord.Guild, user: discord.Member) -> None:
        for course in await self.find_students_courses(guild, user):
            await self.leave_course(guild, user, course)

    async def find_students_courses(self, guild: discord.Guild, user: discord.Member) -> Iterable[CourseEntity]:
        course_codes = list(await self._student_repository.find_all_students_courses((guild.id, user.id)))
        return await self._course_repository.find_courses(course_codes)

    async def find_all_faculties(self) -> Iterable[FacultyEntity]:
        result = []
        async with self._uow.transaction(readonly=True) as trans:
            async for faculties in await self._faculty_repository.find_all(conn=trans.conn):
                result.extend(faculties)
        return result

    async def recover_database(self, guild: discord.Guild) -> int:
        recovered = 0
        async with self._uow.transaction() as trans:
            async for courses in await self._course_repository.find_all(conn=trans.conn):
                for course in courses:
                    if not (channel := await self._find_course_channel(guild, course)):
                        continue
                    for target in channel.overwrites.keys():
                        if isinstance(target, discord.Member):
                            student = StudentEntity(course.faculty, course.code, guild.id, target.id)
                            await self._student_repository.insert(student, conn=trans.conn)
                    recovered += 1
            return recovered

    @staticmethod
    async def _find_course_channel(guild: discord.Guild, course: CourseEntity) -> Optional[discord.TextChannel]:
        course_channel_name = (
            sanitize_channel_name(f"{course.code} {course.name}")
            if course.faculty == "FI" else
            sanitize_channel_name(f"{course.faculty}:{course.code} {course.name}")
        )
        return get(guild.text_channels, name=course_channel_name)