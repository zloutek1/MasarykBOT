import asyncio
import itertools
from collections import Counter

import disnake as discord
from disnake import ButtonStyle
from disnake.ext import commands


class NavigationButton(discord.ui.Button):
    def __init__(self, paginator, to=None, by=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.paginator = paginator
        self.to=to
        self.by=by

    async def callback(self, ctx):
        await ctx.response.defer()
        if self.to is not None:
            await self.paginator.show_page(self.to)
        else:
            page = self.paginator.current_page + self.by
            await self.paginator.show_page(page)

class HelpView(discord.ui.View):
    def __init__(self, paginator, entries):
        super().__init__()

        self.paginator = paginator
        self.add_item(HelpDropdown(paginator, entries))

        self.add_item(NavigationButton(paginator, to=1, label='<<', style=ButtonStyle.secondary))
        self.add_item(NavigationButton(paginator, by=-1, label='Prev', style=ButtonStyle.primary))
        self.add_item(NavigationButton(paginator, by=1, label='Next', style=ButtonStyle.primary))
        self.add_item(NavigationButton(paginator, to=len(entries), label='>>', style=ButtonStyle.secondary))

    async def interaction_check(self, ctx):
        author = self.paginator.ctx.author
        return ctx.author.id == author.id


class HelpDropdown(discord.ui.Select):
    def __init__(self, paginator, entries):
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

    def prepare(self, entries):
        entries = Counter([entry[0] for entry in entries])

        options = []
        for entry, count in entries.items():
            if count == 1:
                options.append(entry)
                continue

            for i in range(count):
                options.append(f"{entry} {i+1}/{count}")

        return options

    async def callback(self, ctx):
        page = self.entries.index(self.values[0]) + 1
        await ctx.response.defer()
        await self.paginator.show_page(page)


class HelpPaginator:
    def __init__(self, help_command, ctx, entries):
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

    def get_bot_page(self, page):
        cog, description, cmds = self.entries[page - 1]
        self.title = f'{cog} Commands'
        self.description = description
        return cmds

    async def show_prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
        return await self.show_page(self.current_page)

    async def show_next_page(self):
        if self.current_page < len(self.entries):
            self.current_page += 1
        return await self.show_page(self.current_page)

    async def show_page(self, page, first=False):
        self.current_page = page

        cmds = self.get_page(page)
        self.prepare_embed(cmds, page)

        if first:
            self.message = await self.ctx.send(embed=self.embed, view=self.view)
        else:
            self.message = await self.message.edit(embed=self.embed)

    def prepare_embed(self, entries, page):
        self.embed.clear_fields()
        self.embed.title = self.title

        self.embed.set_footer(
            text=f'Use "{self.prefix}help command" for more info on a command.')

        cmds = ""
        for entry in entries:
            signature = f'**» {entry.qualified_name} {entry.signature}**\n'
            cmds += signature
        self.embed.description = cmds

        self.embed.set_author(
            name=f'Page {page}/{len(self.entries)}')

    async def paginate(self):
        await self.show_page(1, first=True)

class PaginatedHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(command_attrs={
            'help': 'Shows help about the bot, a command, or a category'
        })

    async def on_help_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(str(error.original))

    def get_command_signature(self, command):
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

    async def send_bot_help(self, mapping):
        def key(cmd):
            return cmd.cog_name or '\u200bNo Category'

        bot = self.context.bot
        entries = await self.filter_commands(bot.commands, sort=True, key=key)
        nested_pages = []
        per_page = 9
        total = 0

        for cog, _commands in itertools.groupby(entries, key=key):
            _commands = sorted(_commands, key=lambda c: c.name)
            if len(_commands) == 0:
                continue

            total += len(_commands)
            actual_cog = bot.get_cog(cog)
            # get the description if it exists (and the cog is valid) or return Empty embed.
            description = (actual_cog and actual_cog.description) or discord.Embed.Empty
            nested_pages.extend(
                (cog, description, _commands[i:i + per_page])
                for i in range(0, len(_commands), per_page)
            )

        # a value of 1 forces the pagination session
        pages = HelpPaginator(self, self.context, nested_pages)
        pages.total_commands = total

        await pages.paginate()

    async def send_cog_help(self, cog):
        entries = await self.filter_commands(cog.get_commands(), sort=True)
        pages = HelpPaginator(self, self.context, entries)
        pages.title = f'{cog.qualified_name} Commands'
        pages.description = cog.description

        await pages.paginate()


    def common_command_formatting(self, page_or_embed, command):
        page_or_embed.title = self.get_command_signature(command)
        if command.description:
            page_or_embed.description = f'{command.description}\n\n{command.help}'
        else:
            page_or_embed.description = command.help or 'No help found...'


    async def send_command_help(self, command):
        # No pagination necessary for a single command.
        embed = discord.Embed(colour=discord.Colour.blurple())
        self.common_command_formatting(embed, command)
        await self.context.send(embed=embed)


    async def send_group_help(self, group):
        subcommands = group.commands
        if len(subcommands) == 0:
            return await self.send_command_help(group)

        entries = await self.filter_commands(subcommands, sort=True)
        pages = HelpPaginator(self, self.context, entries)
        self.common_command_formatting(pages, group)



class Help(commands.Cog):
    """Commands for utilities related to Discord or the Bot itself."""

    def __init__(self, bot):
        self.bot = bot
        self.old_help_command = bot.help_command
        bot.help_command = PaginatedHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self.old_help_command

    @commands.command(hidden=True)
    async def hello(self, ctx):
        """Displays my intro message."""
        await ctx.send('Hello! I\'m a robot! Zloutek1 made me.')


def setup(bot):
    bot.add_cog(Help(bot))
