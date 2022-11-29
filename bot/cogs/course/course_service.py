from enum import auto, Enum
from typing import List, Optional, Dict

import discord
import inject
from discord.ext import commands

from bot.constants import CONFIG
from bot.db import CourseRepository, FacultyRepository
from .registration_context import CourseRegistrationContext
from .trie import Trie
from ...db.muni.course import CourseEntity

DISCORD_CATEGORY_MAX_CHANNELS_LIMIT = 50



class Status(Enum):
    REGISTERED = auto()
    SHOWN = auto()
    UNSIGNED = auto()



class CourseService:
    category_trie = Trie()


    @inject.autoparams('faculty_repository', 'course_repository')
    def __init__(
            self,
            bot: commands.Bot,
            faculty_repository: FacultyRepository,
            course_repository: CourseRepository,
    ) -> None:
        self.bot = bot
        self._faculty_repository = faculty_repository
        self._course_repository = course_repository


    async def load_category_trie(self) -> None:
        courses = await self._course_repository.find_all_courses()
        self.category_trie.insert_all(courses)


    def load_course_registration_channels(self) -> Dict[int, discord.abc.Messageable]:
        result = {}
        for guild_config in CONFIG.guilds:
            if not guild_config.channels.course:
                continue
            channel_id = guild_config.channels.course.registration_channel
            if not (channel := self.bot.get_channel(channel_id)):
                continue
            result[channel.id] = channel
        return result


    async def autocomplete(self, pattern: str) -> List[CourseEntity]:
        return await self._course_repository.autocomplete(f'%{pattern}%')


    @staticmethod
    async def get_course_info(course: CourseEntity) -> Optional[discord.Embed]:
        return discord.Embed(
            color=CONFIG.colors.MUNI_YELLOW,
            title=f"{course.faculty}:{course.code}",
            description=f"{course.name}\n\n{course.url}"
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
            category = await context.create_or_get_course_category(self.category_trie, DISCORD_CATEGORY_MAX_CHANNELS_LIMIT)
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
        pass
