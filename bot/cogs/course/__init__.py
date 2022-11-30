import contextlib
from pathlib import Path
from typing import Dict, List, cast, Optional

import discord
import inject
from discord.app_commands import Choice
from discord.ext import commands
from discord.utils import get

from bot.constants import CONFIG
from bot.db import CourseRepository
from bot.db.muni.course import CourseEntity
from .course_service import CourseService
from ..utils import Context, GuildContext, requires_database


_reg_msg_path = Path(__file__).parent.parent.parent.joinpath('assets/course_registration_message.txt')
with open(_reg_msg_path, 'r') as file:
    COURSE_REGISTRATION_MESSAGE = file.read()


class NotInRegistrationChannel(commands.UserInputError):
    pass


def in_registration_channel():
    def predicate(ctx: Context) -> bool:
        assert isinstance(ctx.cog, CourseCog)
        cog = cast(CourseCog, ctx.cog)
        if ctx.channel.id not in cog.course_registration_channels:
            raise NotInRegistrationChannel(fmt_error(ctx, cog))
        return True


    def fmt_error(ctx: Context, cog: "CourseCog") -> str:
        registration_channel = get(cog.course_registration_channels.values(), guild__id=ctx.guild.id)
        if registration_channel is None:
            return f"You are not in a course registration channel."
        if hasattr(registration_channel, 'mention'):
            return f"You are not in a course registration channel. Please use {registration_channel.mention}"
        return f"You are not in a course registration channel. Please use #{registration_channel}"


    return commands.check(predicate)


class Course(commands.Converter, CourseEntity):
    @classmethod
    @inject.autoparams('course_repository')
    async def convert(cls, ctx: Context, argument: str, course_repository: CourseRepository = None) -> CourseEntity:
        faculty, code = argument.split(':', 1) if ':' in argument else ('FI', argument)
        if not (course := await course_repository.find_by_code(faculty, code)):
            raise commands.BadArgument(f'Course {argument} not found')
        return course



class CourseCog(commands.Cog):
    def __init__(self, bot: commands.Bot, subject_service: CourseService = None) -> None:
        self.bot = bot
        self._service = subject_service or CourseService(bot)
        self.course_registration_channels: Dict[int, discord.abc.Messageable] = {}


    @commands.Cog.listener()
    async def on_ready(self):
        self.course_registration_channels = self._service.load_course_registration_channels()
        await self._service.load_category_trie()


    @commands.hybrid_group(aliases=['subject'])
    @commands.guild_only()
    async def course(self, ctx: GuildContext) -> None:
        pass


    @course.command(aliases=['add', 'show'])
    @in_registration_channel()
    async def join(self, ctx: GuildContext, courses: commands.Greedy[Course]) -> None:
        if len(courses) > 10:
            raise commands.BadArgument('You can only join 10 courses with one command')
        for course in courses:
            status = await self._service.join_course(ctx.guild, ctx.author, course)
            match status:
                case status.REGISTERED: await ctx.send_success(f"Registered course {course.faculty}:{course.code}")
                case status.SHOWN: await ctx.send_success(f"Shown course {course.faculty}:{course.code}")


    @course.command(aliases=['remove', 'hide'])
    @in_registration_channel()
    async def leave(self, ctx: GuildContext, courses: commands.Greedy[Course]) -> None:
        if len(courses) > 10:
            raise commands.BadArgument('You can only leave 10 courses with one command, consider using `!course leave_all`')
        for course in courses:
            await self._service.leave_course(ctx.guild, ctx.author, course)
            await ctx.send(f'Left course {course.faculty}:{course.code}')


    @course.command(aliases=['remove_all', 'hide_all'])
    @in_registration_channel()
    async def leave_all(self, ctx: GuildContext) -> None:
        await self._service.leave_all_courses(ctx.guild, ctx.author)
        await ctx.send(f'Left all courses')


    @course.command()
    async def search(self, ctx: GuildContext, pattern: str) -> None:
        embed = await self._service.search_courses(pattern)
        await ctx.send(embed=embed)


    @course.command()
    async def find(self, ctx: GuildContext, course: Course) -> None:
        embed = await self._service.get_course_info(course)
        await ctx.send(embed=embed)


    @course.command()
    async def profile(self, ctx: GuildContext, member: Optional[discord.Member]) -> None:
        member = ctx.author if member is None else member
        embed = await self._service.get_user_info(ctx.guild, member)
        await ctx.send(embed=embed)


    @join.autocomplete('courses')
    @leave.autocomplete('courses')
    @find.autocomplete('course')
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



@requires_database
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CourseCog(bot))
