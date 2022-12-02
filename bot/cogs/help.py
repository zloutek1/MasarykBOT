import itertools
from collections import Counter
from typing import Any, List, Mapping, Optional, Tuple, TypeVar, Union

import discord as discord
from discord import ButtonStyle, Embed
from discord.ext import commands

from bot.utils import Context, map_range

Page = Tuple[str, str, List[commands.Command[Any, ..., Any]]]  # type: ignore[misc]
BotT = TypeVar('BotT', bound=commands.Bot | commands.AutoShardedBot)


class NavigationButton(discord.ui.Button[Any]):
    def __init__(
            self,
            paginator: "HelpPaginator",
            to: Optional[int] = None,
            by: Optional[int] = None,
            *args: Any,
            **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)

        self.paginator = paginator
        self.to = to
        self.by = by

    async def callback(self, interaction: discord.Interaction) -> Any:
        await interaction.response.defer()
        if self.to is not None:
            return await self.paginator.show_page(self.to)
        elif self.by is not None:
            page = self.paginator.current_page + self.by
            return await self.paginator.show_page(page)


class HelpView(discord.ui.View):
    def __init__(self, paginator: "HelpPaginator", entries: List[Page]) -> None:
        super().__init__()

        self.paginator = paginator
        self.add_item(HelpDropdown(paginator, entries))

        self.add_item(NavigationButton(paginator, to=1, label='<<', style=ButtonStyle.secondary))
        self.add_item(NavigationButton(paginator, by=-1, label='Prev', style=ButtonStyle.primary))
        self.add_item(NavigationButton(paginator, by=1, label='Next', style=ButtonStyle.primary))
        self.add_item(NavigationButton(paginator, to=len(entries), label='>>', style=ButtonStyle.secondary))

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        author = self.paginator.ctx.author
        return interaction.user.id == author.id


class HelpDropdown(discord.ui.Select[HelpView]):
    def __init__(self, paginator: 'HelpPaginator', entries: List[Page]) -> None:
        self.paginator = paginator
        self.entries = self.prepare(entries)

        options = [
            discord.SelectOption(label=entry)
            for entry in self.entries
        ]

        super().__init__(
            placeholder="Jump to page...",
            min_values=1,
            max_values=1,
            options=options
        )

    @staticmethod
    def prepare(entries: List[Page]) -> List[str]:
        _entries = Counter([entry[0] for entry in entries])

        # Dropdown allows maximum of 25 entries
        indexes = set(
            round(map_range(i, 0, len(_entries), 0, min(len(_entries), 25))) for i in range(len(_entries))
        )

        options: List[str] = []
        offset = 1
        for i, (entry, count) in enumerate(_entries.items()):
            if i not in indexes:
                continue

            if count == 1:
                options.append(f"{i + offset}. {entry}")
                continue

            for j in range(count):
                if j != 0:
                    offset += 1
                options.append(f"{i + offset}. {entry} {j + 1}/{count}")

        return options

    async def callback(self, interaction: discord.Interaction) -> Any:
        page = self.entries.index(self.values[0]) + 1
        await interaction.response.defer()
        await self.paginator.show_page(page)


class HelpPaginator:
    def __init__(
            self,
            help_command: "PaginatedHelpCommand",
            ctx: Context,
            entries: List[Page]
    ) -> None:
        self.message: discord.Message | None = None
        self.help_command = help_command
        self.ctx = ctx
        self.prefix = ctx.clean_prefix

        self.entries = entries
        self.current_page = 1
        self.embed = discord.Embed(colour=discord.Colour.blurple())
        self.view = HelpView(self, self.entries)

        self.title = "Help"
        self.description = ""
        self.total_commands = 0
        self.get_page = self.get_bot_page

    def get_bot_page(self, page: int) -> List[commands.Command[Any, ..., Any]]:
        cog, description, cmds = self.entries[page - 1]
        self.title = f'{cog} Commands'
        self.description = description
        return cmds

    async def show_prev_page(self) -> None:
        if self.current_page > 1:
            self.current_page -= 1
        return await self.show_page(self.current_page)

    async def show_next_page(self) -> None:
        if self.current_page < len(self.entries):
            self.current_page += 1
        return await self.show_page(self.current_page)

    async def show_page(self, page: int, first: bool = False) -> None:
        if not (1 <= page <= len(self.entries)):
            return

        self.current_page = page

        cmds = self.get_page(page)
        self.prepare_embed(cmds, page)

        if first:
            self.message = await self.ctx.send(embed=self.embed, view=self.view)
        else:
            self.message = await self.message.edit(embed=self.embed)

    def prepare_embed(self, entries: List[commands.Command[Any, ..., Any]], page: int) -> None:
        self.embed.clear_fields()
        self.embed.title = self.title

        self.embed.set_footer(
            text=f'Use "{self.prefix}help command" for more info on a command.')

        cmds = ""
        for entry in entries:
            signature = self.format_command(entry)
            cmds += signature
        self.embed.description = cmds

        self.embed.set_author(
            name=f'Page {page}/{len(self.entries)}')

    @staticmethod
    def format_command(cmd: commands.Command[Any, ..., Any]) -> str:
        return f'**» {cmd.qualified_name} {cmd.signature}**\n'

    async def paginate(self) -> None:
        await self.show_page(1, first=True)


class PaginatedHelpCommand(commands.HelpCommand):
    context: Context

    def __init__(self) -> None:
        super().__init__(command_attrs={
            'help': 'Shows help about the bot, a command, or a category'
        })

    async def on_help_command_error(self, ctx: commands.Context[BotT], error: commands.CommandError, /) -> None:
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(str(error.original))

    def get_command_signature(self, command: commands.Command[Any, ..., Any]) -> str:
        parent = command.full_parent_name
        if len(command.aliases) > 0:
            aliases = '|'.join(command.aliases)
            fmt = f'[{command.name}|{aliases}]'
            if parent:
                fmt = f'{parent} {fmt}'
            alias = fmt
        else:
            alias = command.name if not parent else f'{parent} {command.name}'
        return f'{alias} {command.signature}'

    async def send_bot_help(
            self,
            _mapping: Mapping[Optional[commands.Cog], List[commands.Command[Any, ..., Any]]]
    ) -> None:
        def key(cmd: commands.Command[Any, ..., Any]) -> str:
            return cmd.cog_name or '\u200bNo Category'

        bot: commands.Bot | commands.AutoShardedBot = self.context.bot
        entries = await self.filter_commands(bot.commands, sort=True, key=key)
        nested_pages: List[Page] = []
        per_page = 9
        total = 0

        for cog, cog_commands in itertools.groupby(entries, key=key):
            sorted_commands = sorted(list(cog_commands), key=lambda c: c.name)
            if len(sorted_commands) == 0:
                continue

            total += len(sorted_commands)
            actual_cog = bot.get_cog(cog)
            description = (actual_cog and actual_cog.description) or ""

            nested_pages.extend(
                (cog, description, sorted_commands[i:i + per_page])
                for i in range(0, len(sorted_commands), per_page)
            )

        # a value of 1 forces the pagination session
        pages = HelpPaginator(self, self.context, nested_pages)
        pages.total_commands = total

        await pages.paginate()

    async def send_cog_help(self, cog: commands.Cog) -> None:
        cmds = await self.filter_commands(cog.get_commands(), sort=True)
        entries: List[Page] = [(cog.qualified_name, '', cmds)]
        pages = HelpPaginator(self, self.context, entries)
        pages.title = f'{cog.qualified_name} Commands'
        pages.description = cog.description

        await pages.paginate()

    def common_command_formatting(
            self,
            page_or_embed: Union[HelpPaginator, Embed],
            command: commands.Command[Any, ..., Any]
    ) -> None:
        page_or_embed.title = self.get_command_signature(command)
        if command.description:
            page_or_embed.description = f'{command.description}\n\n{command.help}'
        else:
            page_or_embed.description = command.help or 'No help found...'

    async def send_command_help(self, command: commands.Command[Any, ..., Any]) -> None:
        # No pagination necessary for a single command.
        embed = discord.Embed(colour=discord.Colour.blurple())
        self.common_command_formatting(embed, command)
        await self.context.send(embed=embed)

    async def send_group_help(self, group: commands.Group[Any, ..., Any]) -> None:
        subcommands = group.commands
        if len(subcommands) == 0:
            await self.send_command_help(group)
            return

        filtered_subcommands = await self.filter_commands(subcommands, sort=True)
        entries = [(group.name, group.description, filtered_subcommands)]

        pages = HelpPaginator(self, self.context, entries)
        self.common_command_formatting(pages, group)

        await pages.paginate()


class HelpCog(commands.Cog):
    """Commands for utilities related to Discord or the Bot itself."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.old_help_command = bot.help_command
        bot.help_command = PaginatedHelpCommand()
        bot.help_command.cog = self

    async def cog_unload(self) -> None:
        self.bot.help_command = self.old_help_command

    @commands.command(hidden=True)
    async def hello(self, ctx: Context) -> None:
        """Displays my intro message."""
        await ctx.send('Hello! I\'m a robot! Zloutek1 made me.')


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))
