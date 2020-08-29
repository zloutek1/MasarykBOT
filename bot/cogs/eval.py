from discord.ext import commands

import json
import aiohttp


class CodeBlock:
    missing_error = 'Missing code block. Please use the following markdown\n\\`\\`\\`language\ncode here\n\\`\\`\\`'

    def __init__(self, argument):
        try:
            block, code = argument.split('\n', 1)
        except ValueError:
            raise commands.BadArgument(self.missing_error)

        if not block.startswith('```') and not code.endswith('```'):
            raise commands.BadArgument(self.missing_error)

        language = block[3:]
        self.command = self.get_command_from_language(language.lower())
        self.source = code.rstrip('`').replace('```', '')

    def get_command_from_language(self, language):
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

        try:
            return cmds[language]
        except KeyError as e:
            if language:
                fmt = f'Unknown language to compile for: {language}'
            else:
                fmt = 'Could not find a language to compile with.'
            raise commands.BadArgument(fmt) from e


class Eval(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="eval", aliases=["e", "coliru"])
    async def coliru(self, ctx, *, code: CodeBlock):
        """Compiles code via Coliru.
        You have to pass in a code block with the language syntax
        either set to one of these:
        - cpp
        - c
        - python
        - py
        - haskell
        Anything else isn't supported. The C++ compiler uses g++ -std=c++14.
        The python support is now 3.5.2.
        Please don't spam this for Stacked's sake.
        """
        payload = {
            'cmd': code.command,
            'src': code.source
        }

        data = json.dumps(payload)

        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.post('http://coliru.stacked-crooked.com/compile', data=data) as resp:
                    if resp.status != 200:
                        await ctx.send('Coliru did not respond in time.')
                        return

                    output = await resp.text(encoding='utf-8')

                    if len(output) < 1992:
                        await ctx.send(f'```\n{output}\n```')
                        return

                    # output is too big so post it in gist
                    async with session.post('http://coliru.stacked-crooked.com/share', data=data) as r:
                        if r.status != 200:
                            await ctx.send('Could not create coliru shared link')
                        else:
                            shared_id = await r.text()
                            await ctx.send(f'Output too big. Coliru link: http://coliru.stacked-crooked.com/a/{shared_id}')

    @coliru.error
    async def coliru_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(CodeBlock.missing_error)


def setup(bot):
    bot.add_cog(Eval(bot))
