from typing import Optional

from discord import Color, Member
from discord.ext import commands
from discord.utils import escape_markdown

from .utils import paginator


class TagPages(paginator.Pages):
    def prepare_embed(self, entries, page, *, first=False):
        body = []
        for i, entry in enumerate(entries):
            body.append(f'**{i+1}.** {entry["name"]}')

        if self.maximum_pages > 1:
            if self.show_entry_count:
                text = f'Page {page}/{self.maximum_pages} ({len(self.entries)} entries)'
            else:
                text = f'Page {page}/{self.maximum_pages}'

            self.embed.set_footer(text=text)

        if self.paginating and first:
            body.append('')
            body.append('Confused? React with \N{INFORMATION SOURCE} for more info.')

        self.embed.description = '\n'.join(body)


class TagName(commands.clean_content):
    def __init__(self, *, lower=False):
        self.lower = lower
        super().__init__()

    async def convert(self, ctx, argument):
        converted = await super().convert(ctx, argument)
        lower = converted.lower().strip()

        if not lower:
            raise commands.BadArgument('Missing tag name.')

        if len(lower) > 100:
            raise commands.BadArgument('Tag name is a maximum of 100 characters.')

        first_word, _, _ = lower.partition(' ')

        # get tag command.
        root = ctx.bot.get_command('tag')
        if first_word in root.all_commands:
            raise commands.BadArgument('This tag name starts with a reserved word.')

        return converted if not self.lower else lower


class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def tag(self, ctx, *, name: TagName(lower=True)):
        tag = await self.bot.db.tags.find(ctx.guild.id, ctx.author.id, name)
        if tag is None:
            tag = await self.bot.db.tags.find(ctx.guild.id, None, name)
        if tag is None:
            return await ctx.send_error(f"Tag not `{name}` found")

        await ctx.send_embed(tag.get('content'),
                        name=tag.get('name') + "\n​",
                        color=Color.blurple())

    @tag.command(aliases=["find"])
    async def search(self, ctx, member: Optional[Member] = None, *, query: commands.clean_content = ""):
        if len(query) < 3:
            return await ctx.send_error('The query length must be at least three characters.')

        member_id = member.id if member else None
        results = await self.bot.db.tags.search(ctx.guild.id, member_id, f"%{query}%")
        if results:
            try:
                pages = TagPages(ctx, entries=results, per_page=20)
            except Exception as err:
                await ctx.send(err)
            else:
                await pages.paginate()
        else:
            await ctx.send(f'No tags containing `{query}` found.')

    @tag.command(aliases=["add", "edit"])
    async def create(self, ctx, name: TagName(lower=True), *, content: commands.clean_content):
        await self.bot.db.tags.insert(ctx.guild.id, ctx.author.id, name, content)
        await ctx.send(f'Tag {name} successfully created/updated.')
        await ctx.invoke(self.tag, name=name)


    @tag.command(aliases=["delete"])
    async def remove(self, ctx, *, name: TagName(lower=True)):
        tag = await self.bot.db.tags.find(ctx.guild.id, ctx.author.id, name)
        if tag is None:
            return await ctx.send_error(f"Tag `{name}` not found")

        await self.bot.db.tags.delete(ctx.guild.id, ctx.author.id, name)
        await ctx.send('Tag successfully deleted.')

    @tag.command(name="list")
    async def _list(self, ctx, *, member: Member = None):
        member = member or ctx.author

        rows = await self.bot.db.tags.findAll(ctx.guild.id, member.id)
        if rows:
            try:
                pages = TagPages(ctx, entries=rows)
                await pages.paginate()
            except Exception as err:
                await ctx.send(err)
        else:
            await ctx.send(f'{member} has no tags.')

    @tag.group(name="public", invoke_without_command=True)
    async def tag_public(self, ctx, *, name: TagName(lower=True)):
        tag = await self.bot.db.tags.find(ctx.guild.id, None, name)
        if tag is None:
            return await ctx.send_error(f"Tag `{name}` not found")

        await ctx.send_embed(tag.get('content'),
                        name=tag.get('name') + "\n​",
                        color=Color.blurple())

    @tag.command(aliases=["clone", "move"])
    async def copy(self, ctx, member: Member, *, name: TagName(lower=True)):
        await self.bot.db.tags.copy(ctx.guild.id, member.id, ctx.author.id, name)
        await ctx.send(f'Tag {name} successfully copied/updated.')
        await ctx.invoke(self.tag_public, name=name)

    @tag.command()
    async def publish(self, ctx, member: Member, *, name: TagName(lower=True)):
        await self.bot.db.tags.copy(ctx.guild.id, member.id, None, name)
        await ctx.send(f'Tag {name} successfully published/updated.')
        await ctx.invoke(self.tag_public, name=name)

    @tag.command()
    async def raw(self, ctx, member: Optional[Member]=None, *, name: TagName(lower=True) = ""):
        member_id = member.id if member else None
        tag = await self.bot.db.tags.find(ctx.guild.id, member_id, name)
        if tag is None:
            return await ctx.send_error(f"Tag `{name}` not found")

        first_step = escape_markdown(tag.get('content'))
        await ctx.safe_send(first_step.replace('<', '\\<'))

    @tag_public.command(name="remove", aliases=["delete"])
    async def public_remove(self, ctx, *, name: TagName(lower=True)):
        tag = await self.bot.db.tags.find(ctx.guild.id, None, name)
        if tag is None:
            return await ctx.send_error("Tag not found")

        await self.bot.db.tags.delete(ctx.guild.id, None, name)
        await ctx.send('Tag successfully deleted.')

    @tag_public.command(name="list")
    async def public_list(self, ctx):
        rows = await self.bot.db.tags.findAll(ctx.guild.id, None)
        if rows:
            try:
                pages = TagPages(ctx, entries=rows)
                await pages.paginate()
            except Exception as err:
                await ctx.send(err)
        else:
            await ctx.send(f'There are no public tags.')

    @commands.group(aliases=["t"], invoke_without_command=True)
    async def tags(self, ctx, *, member: Member = None):
        await ctx.invoke(self._list, member=member)

    @tags.command(name="public")
    async def tags_public(self, ctx):
        await ctx.invoke(self.public_list)

def setup(bot):
    bot.add_cog(Tags(bot))
