import logging
from collections import defaultdict
from textwrap import dedent

from discord import Color, Embed, PermissionOverwrite, HTTPException, Member
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord.errors import NotFound
from discord.utils import get, find

from .utils import constants


log = logging.getLogger(__name__)


ERR_EMBED_BODY_TOO_LONG = 50035
SUBJECT_MESSAGE = {
    "body": dedent("""
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
        Podporované fakulty:
        informatika (FI), filozofická (FF), sociálních studií (FSS), Sportovních studií (FSpS), Přírodovědecká (PřF), Právnická (PrF)
        """).strip(),
    "footer": ":point_down: Zapiš si své předměty zde :point_down:"""
}


class ChannelNotFound(Exception):
    def __init__(self, subject, searched, potential, *args):
        super().__init__(self, *args)
        self.subject = subject
        self.searched = searched
        self.potential = potential

    def __str__(self):
        return (f"channel for subject {self.subject} not found. \n" +
                f"looked for {self.searched}. Did you mean {self.potential}?")


class Subject(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="subject", aliases=["subjects"], invoke_without_command=True)
    async def subject(self, ctx):
        await ctx.send_help(ctx.command)

    @subject.command(name="add")
    @commands.bot_has_permissions(manage_channels=True)
    async def _add(self, ctx, *subject_codes):
        if len(subject_codes) > 10:
            await ctx.send_embed(
                "can add max of 10 channels at once",
                color=constants.MUNI_YELLOW,
                delete_after=10)
            return

        for subject_code in subject_codes:
            await self.add(ctx, subject_code)

    async def add(self, ctx, subject_code):
        if ctx.channel.id not in constants.subject_registration_channels:
            await ctx.send_error("You can't add subjects here", delete_after=5)
            return

        await ctx.safe_delete(delay=5)

        faculty, code = subject_code.split(":", 1) if ":" in subject_code else ["FI", subject_code]
        log.info("User %s adding subject %s:%s", ctx.author, faculty, code)

        if (subject := await self.find_subject(code, faculty)) is None:
            return await ctx.send_embed(
                "Could not find one subject matching the code",
                color=constants.MUNI_YELLOW,
                delete_after=5)

        await self.bot.db.subjects.sign_user(ctx.guild.id, subject.get("code"), ctx.author.id)
        await self.try_to_sign_user_to_channel(ctx, subject)

    @subject.command(name="remove")
    @commands.bot_has_permissions(manage_channels=True)
    async def _remove(self, ctx, *subject_codes):
        if len(subject_codes) > 10:
            await ctx.send_embed(
                "can remove max of 10 channels at once",
                color=constants.MUNI_YELLOW,
                delete_after=10)
            return

        for subject_code in subject_codes:
            await self.remove(ctx, subject_code)

    async def remove(self, ctx, subject_code):
        if ctx.channel.id not in constants.subject_registration_channels:
            await ctx.send_error("You can't remove subjects here", delete_after=5)
            return

        await ctx.safe_delete(delay=5)

        faculty, code = subject_code.split(":", 1) if ":" in subject_code else ["FI", subject_code]

        if not (subject := await self.find_subject(code, faculty)):
            return await ctx.send_embed(
                "Could not find one subject matching the code",
                color=constants.MUNI_YELLOW,
                delete_after=5)

        await self.bot.db.subjects.unsign_user(ctx.guild.id, subject.get("code"), ctx.author.id)

        try:
            channel = await self.lookup_channel(ctx, subject, recreate=False)
            await channel.set_permissions(ctx.author, overwrite=None)
            await ctx.send_embed(
                f"Unsigned from subject {self.subject_to_channel_name(ctx, subject)} successfully",
                color=constants.MUNI_YELLOW,
                delete_after=10)

        except ChannelNotFound as err:
            if err.potential is not None:
                raise err from None

            await ctx.send_embed(
                f"Channel {self.subject_to_channel_name(ctx, subject)} does not exist",
                color=constants.MUNI_YELLOW,
                delete_after=10)

    @subject.command(aliases=["search", "lookup"])
    async def find(self, ctx, pattern):
        faculty, code = pattern.split(":", 1) if ":" in pattern else ["FI", pattern]

        subjects = await self.bot.db.subjects.find(code, faculty)
        grouped_by_term = self.group_by_term(subjects)
        await self.display_list_of_subjects(ctx, grouped_by_term)

    @subject.command()
    async def status(self, ctx, pattern):
        faculty, code = pattern.split(":", 1) if ":" in pattern else ["FI", pattern]

        if not (subject := await self.find_subject(code, faculty)):
            return await ctx.send_embed(
                "Could not find one subject matching the code",
                color=constants.MUNI_YELLOW,
                delete_after=5)

        registers = await self.bot.db.subjects.find_registered(ctx.guild.id, code)
        num_registeres = len(registers.get('member_ids')) if registers else 0
        await ctx.send_embed(f"Subject {subject.get('faculty')}:{subject.get('code')} has {num_registeres} registered")


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

        embed = Embed(description=SUBJECT_MESSAGE['body'], color=Color(0xFFD800))
        embed.set_footer(text=SUBJECT_MESSAGE['footer'])
        await menu_text_channel.send(embed=embed)

    @subject.command()
    @has_permissions(administrator=True)
    async def recover_database(self, ctx):
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if not (rows := await self.is_subject_channel(channel)):
                    continue

                code = rows[0].get("code")
                log.info("database recovery for subject %s started (%s)", channel, guild)

                shown_to = [key.id
                            for (key, value) in channel.overwrites.items()
                            if value.read_messages and isinstance(key, Member)]

                await self.bot.db.subjects.set_channel(ctx.guild.id, code, channel.id)
                if channel.category:
                    await self.bot.db.subjects.set_category(ctx.guild.id, code, channel.category.id)

                for member_id in shown_to:
                    await self.bot.db.subjects.sign_user(ctx.guild.id, code, member_id)
        log.info("database recovery finished")

    @subject.command()
    @has_permissions(administrator=True)
    async def reorder(self, ctx):
        guild = ctx.guild
        for channel in guild.text_channels:
            if not (rows := await self.is_subject_channel(channel)):
                continue

            code = rows[0].get("code")
            if not (row := await self.bot.db.subjects.get_category(guild.id, code)):
                continue

            old_category = channel.category
            new_category_name = row.get("category_name")
            new_category = get(guild.categories, name=new_category_name)
            if not new_category:
                new_category = await guild.create_category(new_category_name)

            await channel.edit(category=new_category)

            if len(old_category.channels) == 0:
                await old_category.delete()

    async def is_subject_channel(self, channel):
        if "-" not in channel.name:
            return

        pattern = channel.name.split("-")[0]
        faculty, code = pattern.split("꞉") if "꞉" in pattern else ["fi", pattern]

        return await self.bot.db.subjects.find(code, faculty)

    async def find_subject(self, code, faculty="FI"):
        subjects = await self.bot.db.subjects.find(code, faculty)
        if len(subjects) != 1:
            return None
        return subjects[0]

    async def try_to_sign_user_to_channel(self, ctx, subject):
        channel_name = self.subject_to_channel_name(ctx, subject)

        try:
            channel = await self.create_or_get_existing_channel(ctx, subject)
        except ChannelNotFound:
            await ctx.send_embed(
                f"Signed to subject {channel_name} successfully, but not enough users to create the subject room",
                color=constants.MUNI_YELLOW,
                delete_after=10)
            return

        await ctx.send_embed(
            f"Signed to subject {channel_name} successfully",
            color=constants.MUNI_YELLOW,
            delete_after=10)
        await channel.set_permissions(ctx.author,
                                        overwrite=PermissionOverwrite(read_messages=True))

    async def create_or_get_existing_channel(self, ctx, subject):
        if await self.should_create_channel(ctx, subject):
            if (channel := await self.try_to_get_existing_channel(ctx, subject)) is not None:
                return channel
            return await self.create_channel(ctx, subject)
        else:
            return await self.lookup_channel(ctx, subject)

    async def try_to_get_existing_channel(self, ctx, subject):
        def is_subject_channel(channel):
            faculty, code = subject.get("faculty"), subject.get("code")
            return (channel.name.startswith(code) or
                    channel.name.startswith(f"{faculty}꞉{code}"))

        channel = find(is_subject_channel, ctx.guild.text_channels)
        if channel is not None:
            await self.bot.db.subjects.set_channel(ctx.guild.id, subject.get("code"), channel.id)
        return channel

    async def should_create_channel(self, ctx, subject):
        registers = await self.bot.db.subjects.find_registered(ctx.guild.id, subject.get("code"))
        serverinfo = await self.bot.db.subjects.find_serverinfo(ctx.guild.id, subject.get("code"))

        return (serverinfo is None and
                len(registers.get("member_ids")) >= constants.NEEDED_REACTIONS)

    async def lookup_channel(self, ctx, subject, recreate=True):
        channel = get(ctx.guild.text_channels, name=self.subject_to_channel_name(ctx, subject))
        if channel is None and recreate:
            channel = await self.remove_channel_from_database_and_retry(ctx, subject)
        if channel is None:
            self.throw_not_found(ctx, subject)
        return channel

    def throw_not_found(self, ctx, subject):
        faculty = subject.get('faculty')
        code = subject.get('code')
        channel_name = self.subject_to_channel_name(ctx, subject)
        potential = find(lambda channel: channel.name.lower().startswith(code.lower()), ctx.guild.text_channels)
        raise ChannelNotFound(subject=f"{faculty}:{code}", searched=channel_name, potential=potential)

    async def remove_channel_from_database_and_retry(self, ctx, subject):
        await self.bot.db.subjects.remove_channel(ctx.guild.id, subject.get("code"))

        subject = await self.find_subject(subject.get("code"), subject.get("faculty"))
        if await self.should_create_channel(ctx, subject):
            return await self.create_channel(ctx, subject)

    @staticmethod
    def subject_to_channel_name(ctx, subject):
        faculty = subject.get("faculty")
        code = subject.get("code")
        name = subject.get("name")
        if faculty == "FI":
            return ctx.channel_name(f'{code} {name}')
        return ctx.channel_name(f'{faculty}꞉{code} {name}')

    async def create_channel(self, ctx, subject):
        show_all = [role
                    for role_id in constants.show_all_subjects_roles
                    if (role := ctx.guild.get_role(role_id))]

        mute = [role
                for role_id in constants.mute_roles
                if (role := ctx.guild.get_role(role_id))]

        overwrites = {
            ctx.guild.default_role: PermissionOverwrite(read_messages=False),
            self.bot.user: PermissionOverwrite(read_messages=True),
            **{role: PermissionOverwrite(read_messages=True) for role in show_all},
            **{role: PermissionOverwrite(send_messages=False) for role in mute}
        }

        category = await self.create_or_get_category(ctx, subject)

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

    async def create_or_get_category(self, ctx, subject):
        row = await self.bot.db.subjects.get_category(ctx.guild.id, subject.get("code"))
        if row:
            category_name = row.get("category_name")
            if category := get(ctx.guild.categories, name=category_name):
                return category
            category = await ctx.guild.create_category(category_name)

        else:
            i = 1
            while True:
                category_name = "{faculty} {i}".format(faculty=subject.get("faculty"), i = i if i != 0 else '').strip()
                if category := get(ctx.guild.categories, name=category_name):
                    if len(category.channels) < 50:
                        return category
                    i += 1
                else:
                    category = await ctx.guild.create_category(category_name)
                    break

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
            if message.embeds[0].description == SUBJECT_MESSAGE['body']:
                return

            if message.embeds[0].color and message.embeds[0].color.value == constants.MUNI_YELLOW:
                await message.delete(delay=5)
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
                    if message.embeds[0].description == SUBJECT_MESSAGE['body']:
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
