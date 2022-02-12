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
    def __init__(self, *, lower=False, allow_empty=False):
        self.lower = lower
        self.allow_empty = allow_empty
        super().__init__()

    async def convert(self, ctx, argument):
        converted = await super().convert(ctx, argument)
        lower = converted.lower().strip()

        if lower == "":
            if self.allow_empty:
                return converted if not self.lower else lower
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

    async def _tag_of(self, ctx, user: Optional[Member], name: TagName(lower=True)):
        tag = await self.bot.db.tags.find(ctx.guild.id, user and user.id, name)
        if tag is None:
            return await ctx.send_error(f"Tag not `{name}` found")

        if len(tag.get('content')) > 1024:
            await ctx.send_error("Content too large. We can send only 1024 characters.")
            return

        await ctx.send_embed(tag.get('content'),
                        name=tag.get('name') + "\n​",
                        color=Color.blurple())

    async def _list_of(self, ctx, user: Optional[Member]):
        rows = await self.bot.db.tags.findAll(ctx.guild.id, user and user.id)
        if not rows:
            await ctx.send(f'There are no tags.')
            return

        try:
            pages = TagPages(ctx, entries=rows)
            await pages.paginate()
        except Exception as err:
            await ctx.send(err)

    async def _search_of(self, ctx, user: Optional[Member], query: str):
        if len(query) < 3:
            return await ctx.send_error('The query length must be at least three characters.')

        results = await self.bot.db.tags.search(ctx.guild.id, user and user.id, f"%{query}%")
        if not results:
            return await ctx.send(f'No tags containing `{query}` found.')

        try:
            pages = TagPages(ctx, entries=results, per_page=20)
        except Exception as err:
            await ctx.send(err)
        else:
            await pages.paginate()

    async def _raw_of(self, ctx, user: Optional[Member], name: TagName(lower=True)):
        tag = await self.bot.db.tags.find(ctx.guild.id, user and user.id, name)
        if tag is None:
            return await ctx.send_error(f"Tag not `{name}` found")

        if len(tag.get('content')) > 1024:
            await ctx.send_error("Content too large. We can send only 1024 characters.")
            return

        first_step = escape_markdown(tag.get('content'))
        await ctx.safe_send(first_step.replace('<', '\\<'))

    ##
    # Public
    ##

    @commands.group(aliases=['t', 'tags'], invoke_without_command=True)
    async def tag(self, ctx, *, name: TagName(lower=True, allow_empty=True) = ""):
        if name == "":
            await ctx.invoke(self.tag_list)
            return
        await self._tag_of(ctx, None, name)

    @tag.command(name="list")
    async def tag_list(self, ctx):
        await self._list_of(ctx, None)

    @tag.command(aliases=["find"])
    async def search(self, ctx, *, query: commands.clean_content = ""):
        await self._search_of(ctx, None, query)

    @tag.command()
    async def raw(self, ctx, *, name: TagName(lower=True) = ""):
        await self._raw_of(ctx, None, name)

    ##
    # User's personal
    ##

    @tag.group(name="my", invoke_without_command=True)
    async def tag_my(self, ctx, *, name: TagName(lower=True, allow_empty=True) = ""):
        if name == "":
            await ctx.invoke(self.my_list)
            return
        await self._tag_of(ctx, ctx.author)

    @tag_my.command(name="list")
    async def my_list(self, ctx):
        await self._list_of(ctx, ctx.author)

    @tag_my.command(name="search", aliases=["find"])
    async def my_search(self, ctx, query: commands.clean_content = ""):
        await self._search_of(ctx, ctx.author, query)

    @tag_my.command()
    async def my_raw(self, ctx, *, name: TagName(lower=True) = ""):
        await self._raw_of(ctx, ctx.author, name)

    @tag_my.command(aliases=["add", "edit"])
    async def create(self, ctx, name: TagName(lower=True), *, content: commands.clean_content):
        if len(content) > 1024:
            await ctx.send_error("Content too large. We can send only 1024 characters.")
            return

        await self.bot.db.tags.insert(ctx.guild.id, ctx.author.id, name, content)
        await ctx.send(f'Tag {name} successfully created/updated.')
        await ctx.invoke(self.tag, name=name)

    @tag_my.command(aliases=["delete"])
    async def remove(self, ctx, *, name: TagName(lower=True)):
        tag = await self.bot.db.tags.find(ctx.guild.id, ctx.author.id, name)
        if tag is None:
            return await ctx.send_error(f"Tag `{name}` not found")

        await self.bot.db.tags.delete(ctx.guild.id, ctx.author.id, name)
        await ctx.send('Tag successfully deleted.')


    @tag_my.command(aliases=["clone", "move"])
    async def copy(self, ctx, member: Member, *, name: TagName(lower=True)):
        tag = await self.bot.db.tags.find(ctx.guild.id, member.id, name)
        if tag is None:
            return await ctx.send_error(f"Tag `{name}` not found")

        await self.bot.db.tags.copy(ctx.guild.id, member.id, ctx.author.id, name)
        await ctx.send(f'Tag {name} successfully copied/updated.')
        await ctx.invoke(self.tag_my, name=name)

    @tag.command()
    @commands.has_role("Admin")
    async def publish(self, ctx, member: Member, *, name: TagName(lower=True)):
        tag = await self.bot.db.tags.find(ctx.guild.id, member.id, name)
        if tag is None:
            return await ctx.send_error(f"Tag `{name}` not found")

        await self.bot.db.tags.copy(ctx.guild.id, member.id, None, name)
        await ctx.send(f'Tag {name} successfully published/updated.')
        await ctx.invoke(self.tag_public, name=name)

    ##
    # Other user's
    ##

    @tag.group(name="of", invoke_without_command=True)
    async def tag_of(self, ctx, member: Member, *, name: TagName(lower=True, allow_empty=True) = ""):
        if name == "":
            await ctx.invoke(self.their_list, member=member)
            return
        await self._tag_of(ctx, member, name)

    @tag_of.command(name="list")
    async def their_list(self, ctx, member: Member):
        await self._list_of(ctx, member)

    @tag_of.command(name="search", aliases=["find"])
    async def their_search(self, ctx, member: Member, *, query: commands.clean_content = ""):
        await self._search_of(ctx, member, query)

    @tag_of.command(mame="raw")
    async def their_raw(self, ctx, member: Member, *, name: TagName(lower=True) = ""):
        await self._raw_of(ctx, member, name)

def setup(bot):
    bot.add_cog(Tags(bot))
