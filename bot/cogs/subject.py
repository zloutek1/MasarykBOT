import logging
from collections import defaultdict
from contextlib import suppress
from textwrap import dedent
from typing import Dict, List, Optional, Tuple

from bot.cogs.utils.context import Context
from bot.cogs.utils.db import Record
from bot.constants import Config
from discord import (CategoryChannel, Color, Embed, HTTPException, Member,
                     Message, PermissionOverwrite, TextChannel)
from discord.errors import NotFound
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord.utils import find, get

log = logging.getLogger(__name__)


ERR_EMBED_BODY_TOO_LONG = 50035
SUBJECT_MESSAGE = {
    "body": dedent("""
        zde si můžete "zapsat" (zobrazit) místnost na tomto discorde pre daný předmět

        :warning: tenhle bot není nijako napojen na IS.MUNI
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
    async def subject(self, ctx: Context):
        await ctx.send_help(ctx.command)

    @subject.command(name="add")
    @commands.bot_has_permissions(manage_channels=True)
    async def add(self, ctx: Context, *subject_codes: str) -> None:
        """
        sign up to a subject channel

        usage:
        !subject add ib000 ib002
        !subject add fi:ib000 ib002
        """

        await ctx.safe_delete(delay=5)

        if len(subject_codes) > 10:
            await self.send_subject_embed(ctx, "can add max of 10 channels at once")
            return

        for subject_code in subject_codes:
            await self.add_subject(ctx, subject_code)

    async def add_subject(self, ctx: Context, code_pattern: str) -> None:
        if not await self._in_subject_channel(ctx):
            return

        faculty, code = self.pattern_to_faculty_code(code_pattern)

        log.info("User %s adding subject %s:%s", ctx.author, faculty, code)

        if (subject := await self.find_subject(code, faculty)) is None:
            await self.send_subject_embed(ctx, "Could not find one subject matching the code")
            return

        await self.bot.db.subjects.sign_user(ctx.guild.id, subject.get("code"), ctx.author.id, faculty=subject.get("faculty"))
        await self.try_to_sign_user_to_channel(ctx, subject)

    @staticmethod
    def pattern_to_faculty_code(subject_code: str) -> Tuple[str, str]:
        if ":" in subject_code:
            faculty, code = subject_code.split(":", 1)
            return faculty, code
        return "FI", subject_code


    @staticmethod
    async def send_subject_embed(ctx: Context, message: str) -> Message:
        return await ctx.send_embed(message,
                             color=Config.colors.MUNI_YELLOW,
                             delete_after=10)


    async def _in_subject_channel(self, ctx: Context) -> bool:
        guild_config = get(Config.guilds, id=ctx.guild.id)
        if ctx.channel.id != guild_config.channels.subject_registration:
            designated_channel = get(ctx.guild.text_channels, id=guild_config.channels.subject_registration)
            if designated_channel:
                await ctx.send_error("You can't add subjects here, use a designated channel: " + designated_channel.mention, delete_after=5)
            else:
                await ctx.send_error("You can't add subjects on this server", delete_after=5)
            return False
        return True

    @subject.command(name="remove")
    @commands.bot_has_permissions(manage_channels=True)
    async def remove(self, ctx: Context, *subject_codes: str) -> None:
        """
        unsign from subjects you have signed up to

        usage:
        !subject remove ib000 ib002
        !subject remove fi:ib000 ib002
        !subject remove all
        """

        await ctx.safe_delete(delay=5)

        if len(subject_codes) > 10:
            await self.send_subject_embed(ctx, "can remove max of 10 channels at once")
            return

        for subject_code in subject_codes:
            await self.remove_subject(ctx, subject_code)

    async def remove_subject(self, ctx: Context, code_pattern: str) -> None:
        if not await self._in_subject_channel(ctx):
            return

        if code_pattern == "all":
            await self.remove_all_subjects(ctx)
            return

        faculty, code = self.pattern_to_faculty_code(code_pattern)

        if not (subject := await self.find_subject(code, faculty)):
            await self.send_subject_embed(ctx, "Could not find one subject matching the code")
            return

        await self.bot.db.subjects.unsign_user(ctx.guild.id, subject.get("code"), ctx.author.id, faculty=subject.get("faculty"))
        await self.try_to_unsign_user_from_channel(ctx, subject)

    async def remove_all_subjects(self, ctx: Context) -> None:
        users_subjects = await self.bot.db.subjects.find_users_subjects(ctx.guild.id, ctx.author.id)
        subject_names = [f'{s.get("faculty")}:{s.get("code")}' for s in users_subjects]

        if len(subject_names) == 0:
            await self.send_subject_embed(ctx, "you have no subjects to unsign from")
            return

        for subject_name in subject_names:
            faculty, code = self.pattern_to_faculty_code(subject_name)
            if not (subject := await self.find_subject(code, faculty)):
                log.info(f"failed to find subject {subject_name} during remove all")
                continue
            await self.try_to_unsign_user_from_channel(ctx, subject)

        await self.bot.db.subjects.unsign_user_from_all(ctx.guild.id, ctx.author.id)
        await self.send_subject_embed(ctx, "unsigned from all subjects: " + ", ".join(subject_names))


    @subject.command(aliases=["search", "lookup"])
    async def find(self, ctx, subject_code: str) -> None:
        faculty, code = self.pattern_to_faculty_code(subject_code)

        subjects = await self.bot.db.subjects.find(code, faculty)
        grouped_by_term = self.group_by_term(subjects)
        await self.display_list_of_subjects(ctx, grouped_by_term)

    @subject.command()
    async def status(self, ctx, subject_code: str) -> None:
        faculty, code = self.pattern_to_faculty_code(subject_code)

        if not (subject := await self.find_subject(code, faculty)):
            await self.send_subject_embed(ctx, "Could not find one subject matching the code")
            return

        registers = await self.bot.db.subjects.find_registered(ctx.guild.id, code, faculty)
        num_registeres = len(registers.get('member_ids')) if registers else 0
        await ctx.send_embed(f"Subject {subject.get('faculty')}:{subject.get('code')} has {num_registeres} registered")


    @subject.command()
    @has_permissions(administrator=True)
    async def resend_subject_message(self, ctx: Context, channel_id: int) -> None:
        guild_config = get(Config.guilds, id=ctx.guild.id)
        if channel_id != guild_config.channels.subject_registration:
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
    async def recover_database(self, ctx: Context) -> None:
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if not (subject := await self.get_subject_from_channel(channel)):
                    continue

                faculty = code = subject.get("faculty")
                code = subject.get("code")
                log.info("database recovery for subject %s started (%s)", channel, guild)

                shown_to = [key.id
                            for (key, value) in channel.overwrites.items()
                            if value.read_messages and isinstance(key, Member)]

                await self.bot.db.subjects.set_channel(ctx.guild.id, code, channel.id, faculty)
                if channel.category:
                    await self.bot.db.subjects.set_category(ctx.guild.id, code, channel.category.id, faculty)

                for member_id in shown_to:
                    await self.bot.db.subjects.sign_user(ctx.guild.id, code, member_id, faculty)
        log.info("database recovery finished")

    @subject.command()
    @has_permissions(administrator=True)
    async def reorder(self, ctx: Context) -> None:
        guild = ctx.guild
        for channel in guild.text_channels:
            if not (subject := await self.get_subject_from_channel(channel)):
                continue

            faculty = subject.get("faculty")
            code = subject.get("code")
            if not (row := await self.bot.db.subjects.get_category(guild.id, code, faculty)):
                continue

            old_category = channel.category
            new_category_name = row.get("category_name")
            new_category = get(guild.categories, name=new_category_name)
            if not new_category:
                new_category = await guild.create_category(new_category_name)

            if new_category != old_category:
                await channel.edit(category=new_category)

            if len(old_category.channels) == 0:
                await old_category.delete()

    async def reorder_channels(self) -> None:
        for guild in self.bot.guilds:
            for category in guild.categories:
                if ':' not in category.name:
                    continue

                ordered = sorted(category.channels, key=lambda c: c.name)
                if category.channels == ordered:
                    continue

                for i, channel in enumerate(ordered):
                    await channel.edit(position=i)

    async def get_subject_from_channel(self, channel: TextChannel) -> Optional[Record]:
        if "-" not in channel.name:
            return None

        pattern = channel.name.split("-")[0]
        faculty, code = pattern.split("꞉") if "꞉" in pattern else ["fi", pattern]

        return self.find_subject(code, faculty)

    async def find_subject(self, code: str, faculty: str="FI") -> Optional[Record]:
        subjects = await self.bot.db.subjects.find(code, faculty)
        if len(subjects) != 1:
            return None
        return subjects[0]

    async def try_to_sign_user_to_channel(self, ctx: Context, subject: Record) -> None:
        channel_name = self.subject_to_channel_name(ctx, subject)

        if not await self.check_if_engough_users_signed(ctx.guild.id, subject):
            log.info("Not enough users signed for subject %s", subject)
            await self.send_subject_embed(ctx, f"Signed to subject {channel_name} successfully, but not enough users to create the subject room")
            return

        channel = await self.create_or_get_existing_channel(ctx, subject)
        await channel.set_permissions(ctx.author,overwrite=PermissionOverwrite(read_messages=True))
        await self.send_subject_embed(ctx, f"Signed to subject {channel_name} successfully")
        log.info("Signed user %s to channel %s", str(ctx.author), channel_name)

    async def try_to_unsign_user_from_channel(self, ctx: Context, subject: Record) -> None:
        try:
            channel = await self.lookup_channel(ctx, subject)
            await channel.set_permissions(ctx.author, overwrite=None)
            await self.send_subject_embed(ctx, f"Unsigned from subject {self.subject_to_channel_name(ctx, subject)} successfully")

        except ChannelNotFound as err:
            await self.send_subject_embed(ctx, f"Channel {self.subject_to_channel_name(ctx, subject)} does not exist")
            if err.potential is not None:
                raise err from None

    async def create_or_get_existing_channel(self, ctx: Context, subject: Record) -> TextChannel:
        if (channel := await self.try_to_get_existing_channel(ctx, subject)) is not None:
            return channel

        return await self.create_channel(ctx, subject)

    async def try_to_get_existing_channel(self, ctx: Context, subject: Record) -> Optional[TextChannel]:
        def is_subject_channel(channel):
            faculty, code = subject.get("faculty").lower(), subject.get("code").lower()
            channel_prefix = channel.name.split("-", 1)[0]
            return (channel_prefix.lower() == code or
                    channel_prefix.lower() == f"{faculty}꞉{code}")

        channel = find(is_subject_channel, ctx.guild.text_channels)
        if channel is not None:
            await self.bot.db.subjects.set_channel(ctx.guild.id, subject.get("code"), channel.id, subject.get("faculty"))
        return channel

    async def check_if_engough_users_signed(self, guild_id: int, subject: Record) -> bool:
        registers = await self.bot.db.subjects.find_registered(guild_id, subject.get("code"), subject.get("faculty"))

        guild_config = get(Config.guilds, id=guild_id)
        return len(registers.get("member_ids")) >= guild_config.NEEDED_REACTIONS

    async def lookup_channel(self, ctx: Context, subject: Record) -> TextChannel:
        def is_subject_channel(channel):
            faculty, code = subject.get("faculty").lower(), subject.get("code").lower()
            return (channel.name.lower().startswith(code+"-") or
                    channel.name.lower().startswith(f"{faculty}꞉{code}-"))

        channel = find(is_subject_channel, ctx.guild.text_channels)
        if channel is None:
            self.throw_not_found(ctx, subject)
        return channel

    def throw_not_found(self, ctx: Context, subject: Record) -> None:
        faculty = subject.get('faculty')
        code = subject.get('code')
        channel_name = self.subject_to_channel_name(ctx, subject)
        potential = find(lambda channel: channel.name.lower().startswith(code.lower()), ctx.guild.text_channels)
        raise ChannelNotFound(subject=f"{faculty}:{code}", searched=channel_name, potential=potential)

    @staticmethod
    def subject_to_channel_name(ctx: Context, subject: Record) -> str:
        faculty = subject.get("faculty")
        code = subject.get("code")
        name = subject.get("name")
        if faculty == "FI":
            return ctx.channel_name(f'{code} {name}')
        return ctx.channel_name(f'{faculty}:{code} {name}')

    async def create_channel(self, ctx: Context, subject: Record) -> TextChannel:
        guild_config = get(Config.guilds, id=ctx.guild.id)

        channel_name = self.subject_to_channel_name(ctx, subject)
        category = await self.create_or_get_category(ctx, subject)
        overwrites = self.get_overwrites_for_new_channel(ctx, guild_config)

        channel = await ctx.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        data = await self.bot.db.channels.prepare_one(channel)
        await self.bot.db.channels.insert([data])

        await self.bot.db.subjects.set_channel(ctx.guild.id, subject.get("code"), channel.id, subject.get("faculty"))
        if category:
            await self.bot.db.subjects.set_category(ctx.guild.id, subject.get("code"), category.id, subject.get("faculty"))

        return channel

    def get_overwrites_for_new_channel(self, ctx: Context, guild_config: Config) -> PermissionOverwrite:
        overwrites = {
            ctx.guild.default_role: PermissionOverwrite(read_messages=False),
            self.bot.user: PermissionOverwrite(read_messages=True)
        }

        show_all = ctx.guild.get_role(guild_config.roles.show_all)
        if show_all is not None:
            overwrites[show_all] = PermissionOverwrite(read_messages=True)

        muted = ctx.guild.get_role(guild_config.roles.muted)
        if muted is not None:
            overwrites[muted] = PermissionOverwrite(send_messages=False)

        return overwrites

    async def create_or_get_category(self, ctx: Context, subject: Record) -> CategoryChannel:
        row = await self.bot.db.subjects.get_category(ctx.guild.id, subject.get("code"), subject.get("faculty"))
        if row:
            return await self.create_or_get_named_category(ctx, row)
        else:
            return await self.create_or_get_unnamed_category(ctx, subject)

    async def create_or_get_named_category(self, ctx: Context, row: Record) -> CategoryChannel:
        category_name = row.get("category_name")
        if category := get(ctx.guild.categories, name=category_name):
            return category

        category = await ctx.guild.create_category(category_name)
        await self.bot.db.categories.insert(await self.bot.db.categories.prepare([category]))

        return category

    async def create_or_get_unnamed_category(self, ctx: Context, subject: Record) -> CategoryChannel:
        i = 0
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
    def group_by_term(subjects: List[Record]) -> Dict[str, List[Record]]:
        grouped_by_term = defaultdict(list)
        for subject in subjects:
            for term in subject.get("terms"):
                grouped_by_term[term].append(subject)
        return grouped_by_term

    async def display_list_of_subjects(self, ctx: Context, grouped_by_term: Dict[str, List[Record]]) -> None:
        def prepare(subject: Record) -> str:
            faculty = subject.get("faculty")
            code = subject.get("code")
            name = subject.get("name")
            url = subject.get("url")
            return f"**[{faculty}:{code}]({url})** {name}"

        def by_term(term: str) -> Tuple[int, str]:
            semester, year = term.split()
            return (int(year), semester)

        embed = Embed(color=Config.colors.MUNI_YELLOW)
        if not grouped_by_term:
            embed.add_field(
                inline=False,
                name="No subjects found",
                value="you can add % to the beginning or the end to match a pattern")

        for term, subjects_in_term in sorted(grouped_by_term.items(), key=lambda x: by_term(x[0]), reverse=True):
            embed.add_field(
                inline=False,
                name=term,
                value="\n".join(prepare(subject) for subject in subjects_in_term))

        try:
            await ctx.send(embed=embed)
        except HTTPException as err:
            if err.code == ERR_EMBED_BODY_TOO_LONG:
                await ctx.send_error("Found too many results to display, please be more specific")
                return
            raise err


    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        if (guild_config := get(Config.guilds, id=message.guild.id)) is None:
            return

        if message.channel.id != guild_config.channels.subject_registration:
            return

        if message.author.id == self.bot.user.id and message.embeds:
            if message.embeds[0].description == SUBJECT_MESSAGE['body']:
                return

            if message.embeds[0].color and message.embeds[0].color.value == Config.colors.MUNI_YELLOW:
                with suppress(NotFound):
                    await message.delete(delay=60)
                return

        with suppress(NotFound):
            await message.delete(delay=0.2)

    async def delete_messages_in_subject_channel(self, channel: TextChannel) -> None:
        async for message in channel.history():
            if message.author.id == self.bot.user.id and message.embeds:
                if message.embeds[0].description == SUBJECT_MESSAGE['body']:
                    continue

            await message.delete()

    async def delete_messages_in_subject_channels(self) -> None:
        subject_registrations = [guild.channels.subject_registration for guild in Config.guilds]
        for channel_id in subject_registrations:
            if not (channel := self.bot.get_channel(channel_id)):
                continue

            await self.delete_messages_in_subject_channel(channel)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.delete_messages_in_subject_channels()
        await self.reorder_channels()

def setup(bot):
    bot.add_cog(Subject(bot))
