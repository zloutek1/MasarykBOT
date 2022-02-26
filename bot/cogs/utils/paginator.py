import asyncio
from typing import List, Tuple, Union, cast

import disnake as discord
from disnake.ext.commands import Paginator as CommandPaginator

from .context import Context


class CannotPaginate(Exception):
    pass


class Pages:
    """Implements a paginator that queries the user for the
    pagination interface.

    Pages are 1-index based, not 0-index based.

    If the user does not reply within 2 minutes then the pagination
    interface exits automatically.
    """

    def __init__(
        self,
        ctx: Context,
        *,
        entries: List[str],
        per_page: int = 12,
        show_entry_count: bool = True,
        title: str = "",
        template: str = "{index}. {entry}"
    ) -> None:
        assert isinstance(ctx.channel, (discord.TextChannel, discord.Thread)), \
               "ERROR: cannot send messagees to the channel"

        self.bot = ctx.bot
        self.entries = entries
        self.message = ctx.message
        self.channel = ctx.channel
        self.author = ctx.author
        self.per_page = per_page
        self.template = template
        pages, left_over = divmod(len(self.entries), self.per_page)
        if left_over:
            pages += 1
        self.maximum_pages = pages
        self.embed = discord.Embed(colour=discord.Colour.blurple())
        self.paginating = len(entries) > per_page
        self.show_entry_count = show_entry_count
        self.reaction_emojis = [
            ('\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}',
             self.first_page),
            ('\N{BLACK LEFT-POINTING TRIANGLE}', self.previous_page),
            ('\N{BLACK RIGHT-POINTING TRIANGLE}', self.next_page),
            ('\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}',
             self.last_page),
            ('\N{INPUT SYMBOL FOR NUMBERS}', self.numbered_page),
            ('\N{BLACK SQUARE FOR STOP}', self.stop_pages),
            ('\N{INFORMATION SOURCE}', self.show_help),
        ]

        if title:
            self.embed.title = title

        if ctx.guild is not None:
            self.permissions = self.channel.permissions_for(ctx.guild.me)
        else:
            self.permissions = self.channel.permissions_for(ctx.bot.user)

        if not self.permissions.embed_links:
            raise CannotPaginate('Bot does not have embed links permission.')

        if not self.permissions.send_messages:
            raise CannotPaginate('Bot cannot send messages.')

        if self.paginating:
            # verify we can actually use the pagination session
            if not self.permissions.add_reactions:
                raise CannotPaginate(
                    'Bot does not have add reactions permission.')

            if not self.permissions.read_message_history:
                raise CannotPaginate(
                    'Bot does not have Read Message History permission.')

    def get_page(self, page: int) -> List[str]:
        base = (page - 1) * self.per_page
        return self.entries[base:base + self.per_page]

    def get_content(self, entries: List[str], page: int, *, first: bool = False) -> str:
        return ""

    def get_embed(self, entries: List[str], page: int, *, first: bool = False) -> discord.Embed:
        self.prepare_embed(entries, page, first=first)
        return self.embed

    def prepare_embed(self, entries: List[str], page: int, *, first: bool = False) -> None:
        p = []
        for index, entry in enumerate(entries, 1 + ((page - 1) * self.per_page)):
            p.append(self.template.format(index=index, entry=entry))

        if self.maximum_pages > 1:
            if self.show_entry_count:
                text = f'Page {page}/{self.maximum_pages} ({len(self.entries)} entries)'
            else:
                text = f'Page {page}/{self.maximum_pages}'

            self.embed.set_footer(text=text)

        if self.paginating and first:
            p.append('')
            p.append(
                'Confused? React with \N{INFORMATION SOURCE} for more info.')

        self.embed.description = '\n'.join(p)

    async def show_page(self, page: int, *, first: bool = False) -> None:
        self.current_page = page
        entries = self.get_page(page)
        content = self.get_content(entries, page, first=first)
        embed = self.get_embed(entries, page, first=first)

        if not self.paginating:
            await self.channel.send(content=content, embed=embed)
            return

        if not first:
            await self.message.edit(content=content, embed=embed)
            return

        self.message = await self.channel.send(content=content, embed=embed)
        for (reaction, _) in self.reaction_emojis:
            if self.maximum_pages == 2 and reaction in ('\u23ed', '\u23ee'):
                # no |<< or >>| buttons if we only have two pages
                # we can't forbid it if someone ends up using it but remove
                # it from the default set
                continue

            await self.message.add_reaction(reaction)

    async def checked_show_page(self, page: int) -> None:
        if page != 0 and page <= self.maximum_pages:
            await self.show_page(page)

    async def first_page(self) -> None:
        """goes to the first page"""
        await self.show_page(1)

    async def last_page(self) -> None:
        """goes to the last page"""
        await self.show_page(self.maximum_pages)

    async def next_page(self) -> None:
        """goes to the next page"""
        await self.checked_show_page(self.current_page + 1)

    async def previous_page(self) -> None:
        """goes to the previous page"""
        await self.checked_show_page(self.current_page - 1)

    async def show_current_page(self) -> None:
        if self.paginating:
            await self.show_page(self.current_page)

    async def numbered_page(self) -> None:
        """lets you type a page number to go to"""
        to_delete: List[discord.Message] = []
        to_delete.append(await self.channel.send('What page do you want to go to?'))

        def message_check(m: discord.Message) -> bool:
            return m.author == self.author and \
                self.channel == m.channel and \
                m.content.isdigit()

        try:
            msg = await self.bot.wait_for('message', check=message_check, timeout=30.0)
        except asyncio.TimeoutError:
            to_delete.append(await self.channel.send('Took too long.'))
            await asyncio.sleep(5)
        else:
            page = int(msg.content)
            to_delete.append(msg)
            if page != 0 and page <= self.maximum_pages:
                await self.show_page(page)
            else:
                to_delete.append(await self.channel.send(f'Invalid page given. ({page}/{self.maximum_pages})'))
                await asyncio.sleep(5)

        try:
            snowflakes_to_delete = cast(List[discord.abc.Snowflake], to_delete)
            await self.channel.delete_messages(snowflakes_to_delete)
        except Exception:
            pass

    async def show_help(self) -> None:
        """shows this message"""
        messages = ['Welcome to the interactive paginator!\n']
        messages.append('This interactively allows you to see pages of text by navigating with '
                        'reactions. They are as follows:\n')

        for (emoji, func) in self.reaction_emojis:
            messages.append(f'{emoji} {func.__doc__}')

        embed = self.embed.copy()
        embed.clear_fields()
        embed.description = '\n'.join(messages)
        embed.set_footer(
            text=f'We were on page {self.current_page} before this message.')
        await self.message.edit(content=None, embed=embed)

        async def go_back_to_current_page() -> None:
            await asyncio.sleep(60.0)
            await self.show_current_page()

        self.bot.loop.create_task(go_back_to_current_page())

    async def stop_pages(self) -> None:
        """stops the interactive pagination session"""
        await self.message.delete()
        self.paginating = False

    def react_check(self, reaction: discord.Reaction, user: Union[discord.User, discord.Member]) -> bool:
        if user is None or user.id != self.author.id:
            return False

        if reaction.message.id != self.message.id:
            return False

        for (emoji, func) in self.reaction_emojis:
            if reaction.emoji == emoji:
                self.match = func
                return True
        return False

    async def paginate(self) -> None:
        """Actually paginate the entries and run the interactive loop if necessary."""
        first_page = self.show_page(1, first=True)
        if not self.paginating:
            await first_page
        else:
            # allow us to react to reactions right away if we're paginating
            self.bot.loop.create_task(first_page)

        while self.paginating:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=self.react_check, timeout=120.0)
            except asyncio.TimeoutError:
                self.paginating = False
                try:
                    await self.message.clear_reactions()
                except Exception:
                    pass
                finally:
                    break

            try:
                await self.message.remove_reaction(reaction, user)
            except Exception:
                pass  # can't remove it so don't bother doing so

            await self.match()
