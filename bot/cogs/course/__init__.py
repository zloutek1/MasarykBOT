import contextlib
from pathlib import Path
from typing import Dict, List, Optional

import discord
import inject
from discord.app_commands import Choice
from discord.ext import commands
from discord.ext.commands._types import Check
from discord.utils import get

from bot.constants import CONFIG
from bot.db import CourseRepository
from bot.db.muni.course import CourseEntity
from bot.utils import Context, GuildContext, requires_database
from .course_service import CourseService
from .fetching import FacultyFetchingService, CourseFetchingService

_reg_msg_path = Path(__file__).parent.parent.parent.joinpath('assets/course_registration_message.txt')
with open(_reg_msg_path, 'r') as file:
    COURSE_REGISTRATION_MESSAGE = file.read()


class NotInRegistrationChannel(commands.UserInputError):
    pass


def in_registration_channel() -> Check[GuildContext]:
    async def predicate(ctx: GuildContext) -> bool:
        cog = ctx.cog
        assert isinstance(cog, CourseCog)
        if ctx.channel.id not in cog.course_registration_channels:
            raise NotInRegistrationChannel(fmt_error(ctx, cog))
        return True

    def fmt_error(ctx: GuildContext, cog: "CourseCog") -> str:
        registration_channel = get(cog.course_registration_channels.values(), guild__id=ctx.guild.id)
        if registration_channel is None:
            return f"You are not in a course registration channel."
        if hasattr(registration_channel, 'mention'):
            return f"You are not in a course registration channel. Please use {registration_channel.mention}"
        return f"You are not in a course registration channel. Please use #{registration_channel}"

    return commands.check(predicate)


class Course(commands.Converter[CourseEntity], CourseEntity):
    @classmethod
    @inject.autoparams('course_repository')
    async def convert(cls, ctx: Context, argument: str, course_repository: CourseRepository) -> CourseEntity:
        faculty, code = argument.split(':', 1) if ':' in argument else ('FI', argument)
        if not (course := await course_repository.find_by_code(faculty, code)):
            raise commands.BadArgument(f'Course {argument} not found')
        return course


class CourseCog(commands.Cog):
    def __init__(
            self,
            bot: commands.Bot,
            course_service: Optional[CourseService] = None,
            faculty_fetching_service: Optional[FacultyFetchingService] = None,
            course_fetching_service: Optional[CourseFetchingService] = None
    ) -> None:
        self.bot = bot
        self._service = course_service or CourseService(bot)
        self._faculty_fetching_service = faculty_fetching_service or FacultyFetchingService()
        self._course_fetching_service = course_fetching_service or CourseFetchingService()
        self.course_registration_channels: Dict[int, discord.abc.Messageable] = {}

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.course_registration_channels = self._service.load_course_registration_channels()
        await self._service.load_category_trie()

    @commands.hybrid_group(aliases=['subject'])
    @commands.guild_only()
    async def course(self, ctx: GuildContext) -> None:
        await ctx.send_help("course")

    @course.command(aliases=['add', 'show'], description="Join a course channel or register as interested")
    @in_registration_channel()
    async def join(self, ctx: GuildContext, courses: commands.Greedy[Course]) -> None:
        if len(courses) > 10:
            raise commands.BadArgument('You can only join 10 courses with one command')
        for course in courses:
            status = await self._service.join_course(ctx.guild, ctx.author, course)
            match status:
                case status.REGISTERED:
                    await ctx.send_success(f"Registered course {course.faculty}:{course.code}")
                case status.SHOWN:
                    await ctx.send_success(f"Shown course {course.faculty}:{course.code}")

    @course.command(aliases=['remove', 'hide'], description="Leave course channel or unregister")
    @in_registration_channel()
    async def leave(self, ctx: GuildContext, courses: commands.Greedy[Course]) -> None:
        if len(courses) > 10:
            raise commands.BadArgument(
                'You can only leave 10 courses with one command, consider using `!course leave_all`')
        for course in courses:
            await self._service.leave_course(ctx.guild, ctx.author, course)
            await ctx.send(f'Left course {course.faculty}:{course.code}')

    @course.command(aliases=['remove_all', 'hide_all'], description="Leave all your course channels")
    @in_registration_channel()
    async def leave_all(self, ctx: GuildContext) -> None:
        await self._service.leave_all_courses(ctx.guild, ctx.author)
        await ctx.send(f'Left all courses')

    @course.command(description="Search courses by partial code")
    async def search(self, ctx: GuildContext, pattern: str) -> None:
        embed = await self._service.search_courses(pattern)
        await ctx.send(embed=embed)

    @course.command(description="Get info about a course")
    async def info(self, ctx: GuildContext, course: Course) -> None:
        embed = await self._service.get_course_info(course, ctx.guild.id)
        await ctx.send(embed=embed)

    @course.command(description="Get student's registered courses")
    async def profile(self, ctx: GuildContext, member: Optional[discord.Member]) -> None:
        member = ctx.author if member is None else member
        embed = await self._service.get_user_info(ctx.guild, member)
        await ctx.send(embed=embed)

    @join.autocomplete('courses')
    @leave.autocomplete('courses')
    @info.autocomplete('course')
    async def course_autocomplete(self, _interaction: discord.Interaction, current: str) -> List[Choice[str]]:
        return [
            Choice(
                name=f"{subject.faculty}:{subject.code} {subject.name}"[:95],
                value=f"{subject.faculty}:{subject.code}"
            )
            for subject in await self._service.autocomplete(current)]

    @course.command()
    @commands.has_permissions(administrator=True)
    async def resend_subject_message(self, ctx: GuildContext) -> None:
        if not (channel := get(self.course_registration_channels.values(), guild__id=ctx.guild.id)):
            return

        embed = discord.Embed(description=COURSE_REGISTRATION_MESSAGE, color=CONFIG.colors.MUNI_YELLOW)
        embed.set_footer(text="👇 Zapiš si své předměty zde 👇")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.channel.id not in self.course_registration_channels:
            return
        if message.embeds and message.embeds[0].description == COURSE_REGISTRATION_MESSAGE:
            return
        with contextlib.suppress(discord.errors.NotFound):
            await message.delete(delay=5.2 if message.embeds else 0.2)

    @course.command()
    @commands.is_owner()
    async def fetch_faculties(self, ctx: Context):
        faculties = await self._faculty_fetching_service.fetch()
        await ctx.reply(f"fetched {len(faculties)} faculties")

    @course.command()
    @commands.is_owner()
    async def fetch_courses(self, ctx: Context):
        courses = await self._course_fetching_service.fetch()
        await ctx.reply(f"fetched {len(courses)} courses")


@requires_database
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CourseCog(bot))
