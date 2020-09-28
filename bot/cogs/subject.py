from collections import defaultdict
from textwrap import dedent

from discord import Color, Embed, PermissionOverwrite, HTTPException
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord.errors import NotFound
from discord.utils import get

from .utils import constants


ERR_EMBED_BODY_TOO_LONG = 50035

SUBJECT_MESSAGE = dedent("""
    :warning: předmět si můžeš zapsat/zrušit každých 5 sekund
    příkazem !subject add/remove <faculty>:<subject_code>
    např.
    ```yaml
    !subject add IB000
    !subject remove IB000
    !subject add FF:CJL09
    !subject remove FF:CJL09
    ```
    na předměty které si můžeš pridat použij !subject search <pattern>%
    např.
    ```yaml
    !subject find IB000
    !subject find IB0%
    ```
    :point_down: Zapiš si své předměty zde :point_down:""").strip()


class Subject(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="subject", aliases=["subjects"], invoke_without_command=True)
    async def subject(self, ctx):
        await ctx.send_help(ctx.command)

    @subject.command()
    @commands.bot_has_permissions(manage_channels=True)
    async def add(self, ctx, pattern):
        if ctx.channel.id not in constants.subject_registration_channels:
            await ctx.send_error("You can't add subjects here", delete_after=5)
            return

        await ctx.safe_delete(delay=5)

        faculty, code = pattern.split(":", 1) if ":" in pattern else ["FI", pattern]

        if (subject := await self.find_subject(code, faculty)) is None:
            return await ctx.send_embed(
                "Could not find one subject matching the code",
                color=constants.MUNI_YELLOW,
                delete_after=5)

        await self.bot.db.subjects.sign_user(ctx.guild.id, subject.get("code"), ctx.author.id)
        await self.try_to_sign_user_to_channel(ctx, subject)

    @subject.command()
    @commands.bot_has_permissions(manage_channels=True)
    async def remove(self, ctx, pattern):
        if ctx.channel.id not in constants.subject_registration_channels:
            await ctx.send_error("You can't remove subjects here", delete_after=5)
            return

        await ctx.safe_delete(delay=5)

        faculty, code = pattern.split(":", 1) if ":" in pattern else ["FI", pattern]

        if not (subject := await self.find_subject(code, faculty)):
            return await ctx.send_embed(
                "Could not find one subject matching the code",
                color=constants.MUNI_YELLOW,
                delete_after=5)

        await self.bot.db.subjects.unsign_user(ctx.guild.id, subject.get("code"), ctx.author.id)
        channel = await self.lookup_channel(ctx, subject, recreate=False)
        await channel.set_permissions(ctx.author, overwrite=None)
        await ctx.send_embed(
            f"Unsigned from subject {self.subject_to_channel_name(ctx, subject)} successfully",
            color=constants.MUNI_YELLOW,
            delete_after=10)

    @subject.command(aliases=["search", "lookup"])
    async def find(self, ctx, pattern):
        faculty, code = pattern.split(":", 1) if ":" in pattern else ["FI", pattern]

        subjects = await self.bot.db.subjects.find(code, faculty)
        grouped_by_term = self.group_by_term(subjects)
        await self.display_list_of_subjects(ctx, grouped_by_term)

    @subject.command()
    @has_permissions(administrator=True)
    async def resend_subject_message(self, ctx, channel_id: int):
        if channel_id not in constants.subject_registration_channels:
            await ctx.send_error("channel not in constants")
            return

        menu_text_channel = self.bot.get_channel(channel_id)
        if not menu_text_channel:
            await ctx.send_error("channel does not exist")
            return

        embed = Embed(description=SUBJECT_MESSAGE, color=Color(0xFFD800))
        await menu_text_channel.send(embed=embed)

    async def find_subject(self, code, faculty="FI"):
        subjects = await self.bot.db.subjects.find(code, faculty)
        if len(subjects) != 1:
            return None
        return subjects[0]

    async def try_to_sign_user_to_channel(self, ctx, subject):
        channel = await self.create_or_get_existing_channel(ctx, subject)
        channel_name = self.subject_to_channel_name(ctx, subject)
        if channel is None:
            await ctx.send_embed(
                f"Signed to subject {channel_name} successfully, but not enough users to create the subject room",
                color=constants.MUNI_YELLOW,
                delete_after=10)
        else:
            await ctx.send_embed(
                f"Signed to subject {channel_name} successfully",
                color=constants.MUNI_YELLOW,
                delete_after=10)
            await channel.set_permissions(ctx.author,
                                          overwrite=PermissionOverwrite(read_messages=True))

    async def create_or_get_existing_channel(self, ctx, subject):
        registers = await self.bot.db.subjects.find_registered(ctx.guild.id, subject.get("code"))
        if self.should_create_channel(registers):
            if (channel := await self.try_to_get_existing_channel(ctx, subject)) is not None:
                return channel
            return await self.create_channel(ctx, subject)
        else:
            return await self.lookup_channel(ctx, subject)

    async def try_to_get_existing_channel(self, ctx, subject):
        channel = get(ctx.guild.text_channels, name=self.subject_to_channel_name(ctx, subject))
        if channel is not None:
            await self.bot.db.subjects.set_channel(ctx.guild.id, subject.get("code"), channel.id)
        return channel

    @staticmethod
    def should_create_channel(registers):
        return (registers.get("channel_id") is None and
                (registers.get("member_ids") is None or
                len(registers.get("member_ids")) >= constants.NEEDED_REACTIONS))

    async def lookup_channel(self, ctx, subject, recreate=True):
        channel = get(ctx.guild.text_channels, name=self.subject_to_channel_name(ctx, subject))
        if channel is None and recreate:
            channel = await self.remove_channel_from_database_and_retry(ctx, subject)
        return channel

    async def remove_channel_from_database_and_retry(self, ctx, subject):
        await self.bot.db.subjects.remove_channel(ctx.guild.id, subject.get("code"))

        subject = await self.find_subject(subject.get("code"))
        if self.should_create_channel(subject):
            return await self.create_channel(ctx, subject)

    @staticmethod
    def subject_to_channel_name(ctx, subject):
        code = subject.get("code")
        name = subject.get("name")
        return ctx.channel_name(f'{code} {name}')

    async def create_channel(self, ctx, subject):
        show_all = [role
                    for role_id in constants.show_all_subjects_roles
                    if (role := ctx.guild.get_role(role_id))]

        overwrites = {
            ctx.guild.default_role: PermissionOverwrite(read_messages=False),
            self.bot.user: PermissionOverwrite(read_messages=True),
            **{role: PermissionOverwrite(read_messages=True) for role in show_all}
        }

        row = await self.bot.db.subjects.get_category(ctx.guild.id, subject.get("code"))
        category_name = row.get("category_name") if row else None
        category = await self.create_or_get_category(ctx, category_name)

        channel_name = self.subject_to_channel_name(ctx, subject)
        channel = await ctx.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )
        data = await self.bot.db.channels.prepare([channel])
        await self.bot.db.channels.insert(data)

        await self.bot.db.subjects.set_channel(ctx.guild.id, subject.get("code"), channel.id)
        if category:
            await self.bot.db.subjects.set_category(ctx.guild.id, subject.get("code"), category.id)

        return channel

    async def create_or_get_category(self, ctx, category_name):
        if not category_name:
            return None
        if category := get(ctx.guild.categories, name=category_name):
            return category
        category = await ctx.guild.create_category(category_name)

        await self.bot.db.categories.insert(await self.bot.db.categories.prepare([category]))

        return category

    @staticmethod
    def group_by_term(subjects):
        grouped_by_term = defaultdict(list)
        for subject in subjects:
            for term in subject.get("terms"):
                grouped_by_term[term].append(subject)
        return grouped_by_term

    async def display_list_of_subjects(self, ctx, grouped_by_term):
        def prepare(subject):
            faculty = subject.get("faculty")
            code = subject.get("code")
            name = subject.get("name")
            url = subject.get("url")
            return f"**[{faculty}:{code}]({url})** {name}"

        embed = Embed(color=constants.MUNI_YELLOW)
        if not grouped_by_term:
            embed.add_field(
                inline=False,
                name="No subjects found",
                value="you can add % to the beginning or the end to match a pattern")

        for term, subjects_in_term in grouped_by_term.items():
            embed.add_field(
                inline=False,
                name=term,
                value="\n".join(prepare(subject) for subject in subjects_in_term))

        try:
            await ctx.send(embed=embed)
        except HTTPException as err:
            if err.code == ERR_EMBED_BODY_TOO_LONG:
                await ctx.send_error("Found too many results to display, please be more specific")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id not in constants.subject_registration_channels:
            return

        if message.author.id == self.bot.user.id and message.embeds:
            if message.embeds[0].description == SUBJECT_MESSAGE:
                return

        try:
            await message.delete(delay=0.2)
        except NotFound:
            pass

    @commands.Cog.listener()
    async def on_ready(self):
        for channel_id in constants.subject_registration_channels:
            if not (channel := self.bot.get_channel(channel_id)):
                continue

            async for message in channel.history():
                if message.author.id == self.bot.user.id and message.embeds:
                    if message.embeds[0].description == SUBJECT_MESSAGE:
                        continue

                await message.delete()

        for guild in self.bot.guilds:
            for category in guild.categories:
                if ':' not in category.name:
                    continue

                ordered = sorted(category.channels, key=lambda c: c.name)
                if category.channels == ordered:
                    continue

                for i, channel in enumerate(ordered):
                    await channel.edit(position=i)


def setup(bot):
    bot.add_cog(Subject(bot))
