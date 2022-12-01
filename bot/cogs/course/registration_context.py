from typing import Optional, Dict

import discord
import inject
from discord.utils import get

from bot.cogs.course.trie import Trie
from bot.utils import sanitize_channel_name
from bot.constants import CONFIG
from bot.db import StudentRepository
from bot.db.muni.course import CourseEntity

MAX_CHANNEL_OVERWRITES = 500



class CourseRegistrationContext:
    @inject.autoparams('student_repository')
    def __init__(
            self,
            guild: discord.Guild,
            user: discord.Member,
            course: CourseEntity,
            student_repository: StudentRepository
    ) -> None:
        self.guild = guild
        self.user = user
        self.course = course
        self._student_repository = student_repository

        assert (guild_config := get(CONFIG.guilds, id=guild.id))
        self.guild_config = guild_config


    @property
    def course_channel_name(self):
        return (sanitize_channel_name(f"{self.course.code} {self.course.name}")
                if self.course.faculty == "FI" else
                sanitize_channel_name(f"{self.course.faculty}:{self.course.code} {self.course.name}"))


    async def register_course(self) -> None:
        await self._student_repository.insert((self.course.faculty, self.course.code, self.guild.id, self.user.id))


    async def unregister_course(self) -> None:
        await self._student_repository.soft_delete((self.course.faculty, self.course.code, self.guild.id, self.user.id))


    def find_course_channel(self) -> Optional[discord.TextChannel]:
        return get(self.guild.text_channels, name=self.course_channel_name)


    async def should_create_course_channel(self) -> bool:
        students = await self._student_repository.count_course_students(
            (self.course.faculty, self.course.code, self.guild.id))
        return students >= self.guild_config.channels.course.MINIMUM_REGISTRATIONS


    async def show_course_channel(self, channel: discord.TextChannel) -> None:
        if role := get(channel.guild.roles, name=f"📖{self.course.code}"):
            await self.user.add_roles(role)
        elif len(channel.overwrites) < MAX_CHANNEL_OVERWRITES:
            await channel.set_permissions(self.user, overwrite=discord.PermissionOverwrite(read_messages=True))
        else:
            raise NotImplementedError


    async def hide_course_channel(self, channel: discord.TextChannel) -> None:
        if role := get(channel.guild.roles, name=f"📖{self.course.code}"):
            await self.user.remove_roles(role)
        else:
            await channel.set_permissions(self.user, overwrite=None)


    async def create_course_channel(self, category: discord.CategoryChannel) -> discord.TextChannel:
        return await self.guild.create_text_channel(
            name=self.course_channel_name,
            category=category,
            overwrites=self._get_overwrites_for_new_channel(),
            topic=f"Místnost pro předmět {self.course.name}"
        )


    def _get_overwrites_for_new_channel(self) -> Dict[discord.Member | discord.Role, discord.PermissionOverwrite]:
        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            self.guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        show_all = self.guild.get_role(self.guild_config.roles.show_all)
        if show_all is not None:
            overwrites[show_all] = discord.PermissionOverwrite(read_messages=True)

        muted = self.guild.get_role(self.guild_config.roles.muted)
        if muted is not None:
            overwrites[muted] = discord.PermissionOverwrite(send_messages=False)

        return overwrites

    async def create_or_get_course_category(
            self,
            category_trie: Trie,
            category_max_channel_limit: int
    ) -> discord.CategoryChannel:
        course_code = f"{self.course.faculty}:{self.course.code}"
        if not (category_name := category_trie.find_prefix_for(course_code, category_max_channel_limit)):
            raise RuntimeError(f'failed to find prefix for {course_code}')

        if category := get(self.guild.categories, name=category_name):
            return category
        return await self.guild.create_category(category_name)
