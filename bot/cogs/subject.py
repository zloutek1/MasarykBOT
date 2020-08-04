from discord import Embed, PermissionOverwrite
from discord.ext import commands
from discord.utils import get

from .utils import constants

from collections import defaultdict


ERR_EMBED_BODY_TOO_LONG = 50035


class Subject(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="subject", aliases=["subjects"], invoke_without_command=True)
    async def subject(self, ctx):
        await ctx.send_help(ctx.command)

    @subject.command()
    async def add(self, ctx, code):
        if (subject := await self.find_subject(code)) is None:
            return await ctx.send_embed(
                "Could not find one subject matching the code",
                color=constants.muni_yellow,
                delete_after=5)

        await self.bot.db.subjects.sign_user(ctx.guild.id, subject.get("code"), ctx.author.id)
        await self.try_to_sign_user_to_channel(ctx, subject)

    @subject.command()
    async def remove(self, ctx, code):
        if not (subject := await self.find_subject(code)):
            return await ctx.send_embed(
                "Could not find one subject matching the code",
                color=constants.muni_yellow,
                delete_after=5)

        await self.bot.db.subjects.unsign_user(ctx.guild.id, subject.get("code"), ctx.author.id)
        channel = await self.lookup_channel(ctx, subject, recreate=False)
        await channel.set_permissions(ctx.author, overwrite=None)
        await ctx.send_embed(f"Unsigned from subject {self.subject_to_channel_name(ctx, subject)} successfully", color=constants.muni_yellow, delete_after=10)

    @subject.command(aliases=["search", "lookup"])
    async def find(self, ctx, code):
        subjects = await self.bot.db.subjects.find(code)
        grouped_by_term = self.group_by_term(subjects)
        await self.display_list_of_subjects(ctx, grouped_by_term)

    async def find_subject(self, code):
        subjects = await self.bot.db.subjects.find(code)
        if len(subjects) != 1:
            return None
        return subjects[0]

    async def try_to_sign_user_to_channel(self, ctx, subject):
        channel = await self.create_or_get_existing_channel(ctx, subject)
        if channel is None:
            await ctx.send_embed(
                f"Signed to subject {self.subject_to_channel_name(ctx, subject)} successfully, but not enough users to create the subject room", color=constants.muni_yellow, delete_after=10)
        else:
            await ctx.send_embed(f"Signed to subject {self.subject_to_channel_name(ctx, subject)} successfully", color=constants.muni_yellow, delete_after=10)
            await channel.set_permissions(ctx.author, overwrite=PermissionOverwrite(read_messages=True))

    async def create_or_get_existing_channel(self, ctx, subject):
        registers = await self.bot.db.subjects.find_registered(ctx.guild.id, subject.get("code"))
        if self.should_create_channel(registers):
            return await self.create_channel(ctx, subject)
        else:
            return await self.lookup_channel(ctx, subject)

    @staticmethod
    def should_create_channel(registers):
        return (registers.get("channel_id") is None and
                len(registers.get("member_ids")) >= constants.needed_reactions)

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
        overwrites = {
            ctx.guild.default_role: PermissionOverwrite(read_messages=False),
            self.bot.user: PermissionOverwrite(read_messages=True)
        }
        channel_name = self.subject_to_channel_name(ctx, subject)
        channel = await ctx.guild.create_text_channel(channel_name, overwrites=overwrites)
        await self.bot.db.subjects.set_channel(ctx.guild.id, subject.get("code"), channel.id)
        return channel

    def group_by_term(self, subjects):
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

        embed = Embed(color=constants.muni_yellow)
        for term, subjects_in_term in grouped_by_term.items():
            embed.add_field(
                inline=False,
                name=term,
                value="\n".join(prepare(subject) for subject in subjects_in_term))

        try:
            await ctx.send(embed=embed)
        except Exception as e:
            if e.code == ERR_EMBED_BODY_TOO_LONG:
                await ctx.send_error("Found too many results to display, please be more specific")


def setup(bot):
    bot.add_cog(Subject(bot))
