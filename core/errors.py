import traceback
import sys
from discord.ext import commands
import discord

from config import BotConfig


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command."""

        if hasattr(ctx.command, 'on_error'):
            return

        ignored = (commands.CommandNotFound, commands.UserInputError)
        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send(f'{ctx.command} has been disabled.')

        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument for {ctx.command}")

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

        tb = traceback.format_exception(type(error), error, error.__traceback__)
        for error_room in BotConfig.error_rooms:
            await self.bot.get_channel(error_room).send("```" + "".join(tb) + "```")


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
    print("Cog loaded: CommandErrorHandler")
