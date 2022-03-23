from typing import List, Optional, cast

from bot.db.tags import TagDao
from bot.db.utils import Record
from disnake import Color, Member
from disnake.ext import commands
from disnake.ext.commands.core import AnyContext
from disnake.utils import escape_markdown

from .utils import paginator
from .utils.context import Context


class TagPages(paginator.Pages):
    def prepare_embed(self, entries: List[Record], page: int, *, first: bool = False) -> None:
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
    def __init__(self, *, lower: bool = True, allow_empty: bool = False) -> None:
        self.lower = lower
        self.allow_empty = allow_empty
        super().__init__()

    async def convert(self, ctx: AnyContext, argument: str) -> str:
        lower = argument.lower().strip()

        if lower == "":
            if self.allow_empty:
                return argument if not self.lower else lower
            raise commands.BadArgument('Missing tag name.')

        if len(lower) > 100:
            raise commands.BadArgument('Tag name is a maximum of 100 characters.')

        first_word, _, _ = lower.partition(' ')

        # get tag command.
        root = ctx.bot.get_command('tag')
        assert isinstance(root, commands.Group), "ERROR: comamnd 'tag' is not a group"

        if first_word in root.all_commands:
            raise commands.BadArgument('This tag name starts with a reserved word.')

        return argument if not self.lower else lower


class Tags(commands.Cog):
    tagDao = TagDao()

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _tag_of(self, ctx: Context, user: Optional[Member], name: str) -> None:
        assert ctx.guild is not None, "ERROR: command can only be invoked inside a guild"

        tag = await self.tagDao.find((ctx.guild.id, user.id if user else None, name))
        if tag is None:
            await ctx.send_error(f"Tag not `{name}` found")
            return

        if len(tag['content']) > 1024:
            await ctx.send_error("Content too large. We can send only 1024 characters.")
            return

        await ctx.send_embed(tag['content'],
                        name=tag['name'] + "\n​",
                        color=Color.blurple())

    async def _list_of(self, ctx: Context, user: Optional[Member]) -> None:
        assert ctx.guild is not None, "ERROR: command can only be invoked inside a guild"

        rows = await self.tagDao.findAll((ctx.guild.id, user.id if user else None))
        if not rows:
            await ctx.send(f'There are no tags.')
            return

        try:
            pages = TagPages(ctx, entries=rows)
            await pages.paginate()
        except Exception as err:
            await ctx.send(err)

    async def _search_of(self, ctx: Context, user: Optional[Member], query: str) -> None:
        assert ctx.guild is not None, "ERROR: command can only be invoked inside a guild"

        if len(query) < 3:
            await ctx.send_error('The query length must be at least three characters.')
            return

        results = await self.tagDao.search((ctx.guild.id, user.id if user else None, f"%{query}%"))
        if not results:
            await ctx.send(f'No tags containing `{query}` found.')
            return

        try:
            pages = TagPages(ctx, entries=results, per_page=20)
        except Exception as err:
            await ctx.send(err)
        else:
            await pages.paginate()

    async def _raw_of(self, ctx: Context, user: Optional[Member], name: str) -> None:
        assert ctx.guild is not None, "ERROR: command can only be invoked inside a guild"

        tag = await self.tagDao.find((ctx.guild.id, user.id if user else None, name))
        if tag is None:
            await ctx.send_error(f"Tag not `{name}` found")
            return

        if len(tag['content']) > 1024:
            await ctx.send_error("Content too large. We can send only 1024 characters.")
            return

        first_step = escape_markdown(tag['content'])
        await ctx.safe_send(first_step.replace('<', '\\<'))

    ##
    # Public
    ##

    @commands.group(aliases=['t', 'tags'], invoke_without_command=True)
    async def tag(self, ctx: Context, *, name: TagName(allow_empty=True) = "") -> None: # type: ignore[valid-type]
        name = cast(str, name)
        if name == "":
            await ctx.invoke(self.tag_list)
            return
        await self._tag_of(ctx, None, name)

    @tag.command(name="list")
    async def tag_list(self, ctx: Context) -> None:
        await self._list_of(ctx, None)

    @tag.command(aliases=["find"])
    async def search(self, ctx: Context, *, query: commands.clean_content = "") -> None: # type: ignore[assignment]
        await self._search_of(ctx, None, cast(str, query))

    @tag.command()
    async def raw(self, ctx: Context, *, name: TagName() = "") -> None: # type: ignore[valid-type]
        await self._raw_of(ctx, None, cast(str, name))

    ##
    # User's personal
    ##

    @tag.group(name="my", invoke_without_command=True)
    async def tag_my(self, ctx: Context, *, name: TagName(allow_empty=True) = "") -> None: # type: ignore[valid-type]
        assert isinstance(ctx.author, Member), "ERROR: user must be a member of a guild"
        name = cast(str, name)

        if name == "":
            await ctx.invoke(self.my_list)
            return
        await self._tag_of(ctx, ctx.author, name)

    @tag_my.command(name="list")
    async def my_list(self, ctx: Context) -> None:
        assert isinstance(ctx.author, Member), "ERROR: user must be a member of a guild"
        await self._list_of(ctx, ctx.author)

    @tag_my.command(name="search", aliases=["find"])
    async def my_search(self, ctx: Context, query: commands.clean_content = "") -> None: # type: ignore[assignment]
        assert isinstance(ctx.author, Member), "ERROR: user must be a member of a guild"
        await self._search_of(ctx, ctx.author, cast(str, query))

    @tag_my.command()
    async def my_raw(self, ctx: Context, *, name: TagName() = "") -> None: # type: ignore[valid-type]
        assert isinstance(ctx.author, Member), "ERROR: user must be a member of a guild"
        await self._raw_of(ctx, ctx.author, cast(str, name))

    @tag_my.command(aliases=["add", "edit"])
    async def create(self, ctx: Context, name: TagName(), *, content: commands.clean_content) -> None: # type: ignore[valid-type]
        assert ctx.guild is not None, "ERROR: command can only be invoked inside a guild"
        _name = cast(str, name)
        _content = cast(str, content)

        if len(_content) > 1024:
            await ctx.send_error("Content too large. We can send only 1024 characters.")
            return

        await self.tagDao.insert([(ctx.guild.id, ctx.author.id, _name, _content)])
        await ctx.send(f'Tag {_name} successfully created/updated.')
        await ctx.invoke(self.tag, name=_name)

    @tag_my.command(aliases=["delete"])
    async def remove(self, ctx: Context, *, name: TagName()) -> None: # type: ignore[valid-type]
        assert ctx.guild is not None, "ERROR: command can only be invoked inside a guild"
        _name = cast(str, name)

        tag = await self.tagDao.find((ctx.guild.id, ctx.author.id, _name))
        if tag is None:
            await ctx.send_error(f"Tag `{_name}` not found")
            return

        await self.tagDao.soft_delete((ctx.guild.id, ctx.author.id, _name))
        await ctx.send('Tag successfully deleted.')


    @tag_my.command(aliases=["clone", "move"])
    async def copy(self, ctx: Context, member: Member, *, name: TagName()) -> None: # type: ignore[valid-type]
        assert ctx.guild is not None, "ERROR: command can only be invoked inside a guild"
        _name = cast(str, name)

        tag = await self.tagDao.find((ctx.guild.id, member.id, _name))
        if tag is None:
            await ctx.send_error(f"Tag `{_name}` not found")
            return

        await self.tagDao.copy((ctx.guild.id, member.id, ctx.author.id, _name))
        await ctx.send(f'Tag {_name} successfully copied/updated.')
        await ctx.invoke(self.tag_my, name=_name)

    @tag.command()
    @commands.has_role("Admin")
    async def publish(self, ctx: Context, member: Member, *, name: TagName()) -> None: # type: ignore[valid-type]
        assert ctx.guild is not None, "ERROR: command can only be invoked inside a guild"
        _name = cast(str, name)

        tag = await self.tagDao.find((ctx.guild.id, member.id, _name))
        if tag is None:
            await ctx.send_error(f"Tag `{_name}` not found")
            return

        await self.tagDao.copy((ctx.guild.id, member.id, None, _name))
        await ctx.send(f'Tag {_name} successfully published/updated.')
        await ctx.invoke(self.tag_list, name=_name)

    ##
    # Other user's
    ##

    @tag.group(name="of", invoke_without_command=True)
    async def tag_of(self, ctx: Context, member: Member, *, name: TagName(allow_empty=True) = "") -> None: # type: ignore[valid-type]
        if name == "":
            await ctx.invoke(self.their_list, member=member)
            return
        await self._tag_of(ctx, member, cast(str, name))

    @tag_of.command(name="list")
    async def their_list(self, ctx: Context, member: Member) -> None:
        await self._list_of(ctx, member)

    @tag_of.command(name="search", aliases=["find"])
    async def their_search(self, ctx: Context, member: Member, *, query: commands.clean_content = "") -> None: # type: ignore[assignment]
        await self._search_of(ctx, member, cast(str, query))

    @tag_of.command(mame="raw")
    async def their_raw(self, ctx: Context, member: Member, *, name: TagName() = "") -> None: # type: ignore[valid-type]
        await self._raw_of(ctx, member, cast(str, name))

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Tags(bot))
