from discord import Member, Color
from discord.ext import commands

from .utils import paginator


class TagPages(paginator.Pages):
    def prepare_embed(self, entries, page, *, first=False):
        p = []
        for index, entry in enumerate(entries, 1 + ((page - 1) * self.per_page)):
            p.append(f'**•** {entry["name"]}')

        if self.maximum_pages > 1:
            if self.show_entry_count:
                text = f'Page {page}/{self.maximum_pages} ({len(self.entries)} entries)'
            else:
                text = f'Page {page}/{self.maximum_pages}'

            self.embed.set_footer(text=text)

        if self.paginating and first:
            p.append('')
            p.append('Confused? React with \N{INFORMATION SOURCE} for more info.')

        self.embed.description = '\n'.join(p)


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
        tag = await self.bot.db.tags.get_tag(ctx.guild.id, name)
        if tag is None:
            return await ctx.send_error("Tag not found")

        await ctx.send_embed(tag.get('content'), name=tag.get('name') + "\n​", color=Color.blurple())

    @tag.command(aliases=["add"])
    async def create(self, ctx, name: TagName(lower=True), *, content: commands.clean_content):
        created_successfully = await self.bot.db.tags.create_tag(ctx.guild.id, ctx.author.id, name, content)
        if created_successfully:
            await ctx.send(f'Tag {name} successfully created.')
        else:
            await ctx.send(f'Could not create tag, probably already exists.')

    @tag.command(aliases=["delete"])
    async def remove(self, ctx, *, name: TagName(lower=True)):
        tag = await self.bot.db.tags.get_tag(ctx.guild.id, name)

        if tag is None:
            return await ctx.send_error("Tag not found")

        status = await self.bot.db.tags.delete_tag(ctx.guild.id, ctx.author.id, name)
        await ctx.send('Tag successfully deleted.')

    @tag.command()
    async def edit(self, ctx, name: TagName(lower=True), *, content: commands.clean_content):
        status = await self.bot.db.tags.edit_tag(ctx.guild.id, ctx.author.id, name, content)

        # the status returns UPDATE <count>
        # if the <count> is 0, then nothing got updated
        # probably due to the WHERE clause failing

        if status[-1] == '0':
            await ctx.send_error('Could not edit that tag. Are you sure it exists and you own it?')
        else:
            await ctx.send('Successfully edited tag.')

    @tag.command(pass_context=True)
    async def raw(self, ctx, *, name: TagName(lower=True)):
        tag = await self.bot.db.tags.get_tag(ctx.guild.id, name)

        first_step = discord.utils.escape_markdown(tag.get('content'))
        await ctx.safe_send(first_step.replace('<', '\\<'), escape_mentions=False)

    @tag.command()
    async def search(self, ctx, *, query: commands.clean_content):
        if len(query) < 3:
            return await ctx.send('The query length must be at least three characters.')

        results = await self.bot.db.tags.find_tags(ctx.guild.id, query)
        if results:
            try:
                p = TagPages(ctx, entries=results, per_page=20)
            except Exception as e:
                await ctx.send(e)
            else:
                await ctx.release()
                await p.paginate()
        else:
            await ctx.send('No tags found.')

    @tag.command(name='list')
    async def _list(self, ctx, *, member: Member = None):
        member = member or ctx.author

        rows = await self.bot.db.tags.select(ctx.guild.id, member.id)
        if rows:
            try:
                p = TagPages(ctx, entries=rows)
                await p.paginate()
            except Exception as e:
                await ctx.send(e)
        else:
            await ctx.send(f'{member} has no tags.')

    @commands.command(aliases=["t"])
    async def tags(self, ctx, *, member: Member = None):
        await ctx.invoke(self._list, member=member)


def setup(bot):
    bot.add_cog(Tags(bot))
