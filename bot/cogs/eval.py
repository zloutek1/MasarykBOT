from abc import ABC, abstractmethod
import io
import json
from typing import Dict, List, Optional

import aiohttp
import discord
from discord.ext import commands

from bot.utils import Context



class CodeBlock:
    missing_error = ('Missing code block. Please use the following markdown\n' +
                     '\\`\\`\\`language\ncode here\n\\`\\`\\`')

    def __init__(self, argument: str) -> None:
        try:
            block, code = argument.split('\n', 1)
        except ValueError as err:
            raise commands.BadArgument(self.missing_error) from err

        if not block.startswith('```') and not code.endswith('```'):
            raise commands.BadArgument(self.missing_error)

        self.language = block[3:].lower()
        self.source = code.rstrip('`').replace('```', '')


class EvalService(ABC):
    @abstractmethod
    def supports_language(self, language: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    async def eval(self, ctx: Context, *, code: CodeBlock) -> str:
        raise NotImplementedError()


class ColiruService(EvalService):
    @property
    def commands(self) -> Dict[str, str]:
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

    def supports_language(self, language: str) -> bool:
        return language in self.commands

    async def eval(self, ctx: Context, *, code: CodeBlock) -> str:
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
            'cmd': self.commands[code.language],
            'src': code.source
        }

        data = json.dumps(payload)

        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                return await self.compile(session, data)

    @staticmethod
    async def compile(session: aiohttp.ClientSession, data: str) -> str:
        headers = {'content-type': 'application/json'}
        async with session.post('http://coliru.stacked-crooked.com/compile', data=data, headers=headers) as resp:
            if resp.status != 200:
                return 'Coliru did not respond in time.'

            output = await resp.text(encoding='utf-8')

            return output


class AplCompilingService(EvalService):
    @staticmethod
    def supports_language(language: str) -> bool:
        return language == "apl"

    async def eval(self, ctx: Context, *, code: CodeBlock) -> str:
        payload = [
            "",
            0,
            "",
            code.source.strip()
        ]

        data = json.dumps(payload)

        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                return await self.compile(session, data)

    @staticmethod
    async def compile(session: aiohttp.ClientSession, data: str) -> str:
        headers = {'content-type': 'application/json'}
        async with session.post('https://tryapl.org/Exec', data=data, headers=headers) as resp:
            if resp.status != 200:
                return 'TryApl did not respond in time.'

            output = await resp.json(encoding='utf-8')

            return '\n'.join(output[3])


class EvalCog(commands.Cog):
    def __init__(
            self,
            bot: commands.Bot,
            coliru_service: ColiruService = ColiruService(),
            apl_service: AplCompilingService = AplCompilingService()
    ) -> None:
        self.bot = bot
        self.coliru_service = coliru_service
        self.apl_service = apl_service

    @commands.command(name="eval", aliases=["coliru"])
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def eval(self, ctx: Context, *, code: CodeBlock) -> None:
        compilers: List[EvalService] = [self.coliru_service, self.apl_service]
        for compiler in compilers:
            if compiler.supports_language(code.language):
                response = await compiler.eval(ctx, code=code)
                return await self.display_result(ctx, code, response)
        raise commands.BadArgument("unsupported language: " + code.language)

    @staticmethod
    async def display_result(ctx: Context, code: CodeBlock, response: str) -> None:
        embed = discord.Embed(color=discord.Color.green())
        file: Optional[discord.File] = None

        if len(code.source) < 1024:
            embed.add_field(name='source', value=f'```{code.language}\n{code.source}\n```', inline=False)
        if len(response) < 1024:
            embed.add_field(name='response', value=f'```{code.language}\n{response}\n```', inline=False)
        else:
            fp = io.BytesIO(response.encode('utf-8'))
            file = discord.File(fp=fp, filename='eval-result.txt')

        if embed.fields:
            await ctx.send(embed=embed, file=file)
        elif file:
            await ctx.send(file=file)
        else:
            await ctx.send_error('fail to display result')


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EvalCog(bot))
