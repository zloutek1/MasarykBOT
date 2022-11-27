import discord
import inject
from discord.utils import get

from bot.constants import CONFIG
from bot.db.muni import StudentRepository
from bot.db.muni.course import CourseEntity



class CourseRegistrationContext:
    @inject.autoparams('student_repository')
    def __init__(
            self,
            guild: discord.Guild,
            user: discord.User,
            course: CourseEntity,
            student_repository: StudentRepository
    ) -> None:
        self.guild = guild
        self.user = user
        self.course = course
        self._student_repository = student_repository

        assert (guild_config := get(CONFIG.guilds, id=guild.id))
        self.guild_config = guild_config


    async def register_course(self) -> None:
        await self._student_repository.insert((self.course.faculty, self.course.code, self.guild.id, self.user.id))


    async def unregister_course(self):
        await self._student_repository.soft_delete((self.course.faculty, self.course.code, self.guild.id, self.user.id))


    async def find_course_channel(self):
        pass


    async def should_create_course_channel(self) -> bool:
        students = await self._student_repository.count_course_students((self.course.faculty, self.course.code, self.guild.id))
        return students >= self.guild_config.channels.course.MINIMUM_REGISTRATIONS


    async def create_course_channel(self):
        channel_name = f"{self.course.faculty}:{self.course.code}" if self.course.faculty != "FI" else self.course.code


    async def show_course_channel(self, channel):
        pass


    async def hide_course_channel(self, channel):
        pass
