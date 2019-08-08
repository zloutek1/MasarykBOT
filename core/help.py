import discord
from discord.ext import commands
from discord.ext.commands import Bot, has_permissions

import itertools

import core.utils.get
from core.utils.paginator import Pages


class Help(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

        self.bot.remove_command("help")

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    @has_permissions(add_reactions=True, embed_links=True)
    async def help(self, ctx, *, command=None):
        """Gets all cogs and commands of mine."""
        def key(c):
            return c.cog_name or '\u200bMisc'

        if not command:
            entries = []
            commands = sorted(ctx.bot.commands, key=key)
            for cog, commands in itertools.groupby(commands, key=key):
                plausible = [cmd for cmd in commands if (await self._can_run(cmd, ctx)) and not cmd.hidden]
                if len(plausible) == 0:
                    continue

                for entry in plausible:
                    entries.append(self._command_signature(entry))

            p = Pages(ctx, entries=entries, per_page=10, title="Commands", template="**»** {entry}")
            await p.paginate()

        else:
            plausible = [cmd for cmd in ctx.bot.commands if (await self._can_run(cmd, ctx)) and not cmd.hidden]
            entry = core.utils.get(plausible, name=command)

            if entry:
                p = Pages(ctx, entries=[self._command_signature(entry)], per_page=10, title="Command", template="**»** {entry}")
                await p.paginate()

            else:
                embed = discord.Embed(title="Help Error", description=f"Command {command} not found. Try !help to get list of available commands.", color=discord.Color.red())
                await ctx.send(embed=embed)

    @staticmethod
    async def _can_run(cmd, ctx):
        try:
            return await cmd.can_run(ctx)
        except:
            return False

    @staticmethod
    def _command_signature(cmd):
        # this is modified from discord.py source
        # which I wrote myself lmao

        result = [cmd.qualified_name]
        if cmd.usage:
            result.append(cmd.usage)
            return ' '.join(result)

        params = cmd.clean_params
        if not params:
            return ' '.join(result)

        for name, param in params.items():
            if param.default is not param.empty:
                # We don't want None or '' to trigger the [name=value] case and instead it should
                # do [name] since [name=None] or [name=] are not exactly useful for the user.
                should_print = param.default if isinstance(param.default, str) else param.default is not None
                if should_print:
                    result.append(f'[{name}={param.default!r}]')
                else:
                    result.append(f'[{name}]')
            elif param.kind == param.VAR_POSITIONAL:
                result.append(f'[{name}...]')
            else:
                result.append(f'<{name}>')

        return ' '.join(result)


def setup(bot):
    bot.add_cog(Help(bot))
    print("Cog loaded: Help")
