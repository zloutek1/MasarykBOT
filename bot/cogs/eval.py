import json
import aiohttp
from asyncio import TimeoutError

from discord.ext import commands

def get_cmds():
    cmds = {
        'cpp': 'g++ -std=c++1z -O2 -Wall -Wextra -pedantic -pthread main.cpp -lstdc++fs && ./a.out',
        'c': 'mv main.cpp main.c && gcc -std=c11 -O2 -Wall -Wextra -pedantic main.c && ./a.out',
        'python': 'python3 main.cpp',
        'haskell': 'runhaskell main.cpp'
    }

    for alias in ('cc', 'h', 'c++', 'h++', 'hpp'):
        cmds[alias] = cmds['cpp']

    cmds['py'] = cmds['python']
    cmds['hs'] = cmds['haskell']
    return cmds

class CodeBlock:
    missing_error = ('Missing code block. Please use the following markdown\n' +
                     '\\`\\`\\`language\ncode here\n\\`\\`\\`')

    def __init__(self, argument):
        try:
            block, code = argument.split('\n', 1)
        except ValueError as err:
            raise commands.BadArgument(self.missing_error) from err

        if not block.startswith('```') and not code.endswith('```'):
            raise commands.BadArgument(self.missing_error)

        language = block[3:]
        self.command = self.get_command_from_language(language.lower())
        self.source = code.rstrip('`').replace('```', '')

    @staticmethod
    def get_command_from_language(language):
        try:
            return get_cmds()[language]
        except KeyError as err:
            if language:
                fmt = f'Unknown language to compile for: {language}'
            else:
                fmt = 'Could not find a language to compile with.'
            raise commands.BadArgument(fmt) from err


class Eval(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="eval", aliases=["e", "coliru"])
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def coliru(self, ctx, *, code: CodeBlock):
        """Compiles code via Coliru.
        You have to pass in a code block with the language syntax
        either set to one of these:
        - cpp
        - c
        - python / py
        - haskell / hs
        Anything else isn't supported. The C++ compiler uses g++ -std=c++17.
        Please don't spam this for Stacked's sake.
        """
        payload = {
            'cmd': code.command,
            'src': code.source
        }

        data = json.dumps(payload)

        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                result = await self.coliru_compile(session, data)

        await self.display(ctx, result)

    async def coliru_compile(self, session, data):
        async with session.post('http://coliru.stacked-crooked.com/compile', data=data) as resp:
            if resp.status != 200:
                return 'Coliru did not respond in time.'

            output = await resp.text(encoding='utf-8')

            if len(output) < 1992:
                return output

            # output is too big so post it in gist
            return await self.coliru_shorten(session, data)

    @staticmethod
    async def coliru_shorten(session, data):
        async with session.post('http://coliru.stacked-crooked.com/share', data=data) as response:
            if response.status != 200:
                return 'Could not create coliru shared link'
            else:
                shared_id = await response.text()
                link = f'http://coliru.stacked-crooked.com/a/{shared_id}'
                return f'Output too big. Coliru link: {link}'

    @coliru.error
    async def coliru_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send_error(error)
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send_error(CodeBlock.missing_error)

    async def display(self, ctx, result):
        message = await ctx.safe_send(result if result else "no result")
        await message.add_reaction('\N{WASTEBASKET}')
        await self.wait_for_reaction_or_clear(ctx, message)

    async def wait_for_reaction_or_clear(self, ctx, message):
        def react_check(reaction, user):
            if user is None or user.id != ctx.author.id:
                return False

            if reaction.message.id != message.id:
                return False

            return reaction.emoji == '\N{WASTEBASKET}'

        try:
            await self.bot.wait_for('reaction_add', check=react_check, timeout=120.0)
            await message.delete()
        except asyncio.TimeoutError:
            await message.clear_reactions()


def setup(bot):
    bot.add_cog(Eval(bot))
