from discord import Color, Embed
from discord.ext import commands
import time
import logging

import ast
from astpretty import pprint
import re

import multiprocessing


class EvalError(Exception):
    pass


class Evaluator:
    allowed_imports = [
        "math", "string", "datetime", "random"
    ]

    allowed_builtins = {
        'abs': abs, 'all': all, 'any': any, 'bin': bin, 'bool': bool,
        'chr': chr, 'dict': dict, 'divmod': divmod, 'enumerate': enumerate,
        'filter': filter, 'float': float, 'format': format,
        'frozenset': frozenset, 'hash': hash, 'hex': hex, 'id': id,
        'int': int, 'isinstance': isinstance, 'iter': iter, 'len': len,
        'list': list, 'map': map, 'max': max, 'min': min, 'next': next,
        'object': object, 'oct': oct, 'ord': ord, 'pow': pow, 'range': range,
        'repr': repr, 'reversed': reversed, 'round': round, 'set': set,
        'slice': slice, 'sorted': sorted, 'str': str, 'sum': sum,
        'tuple': tuple, 'zip': zip, 'Exception': Exception,
        '__import__': __import__
    }

    def __init__(self):
        self.allowed_builtins["print"] = self.print

        from io import StringIO
        self.out = StringIO()

    def print(self, *args, **kwargs):
        import sys

        sys.stdout = self.out
        print(*args, **kwargs)
        sys.stdout = sys.__stdout__

    class Transformer(ast.NodeTransformer):
        def visit_Import(self, node):
            for name in map(lambda imp: imp.name, node.names):
                if name not in Evaluator.allowed_imports:
                    raise EvalError("unsuported import")
            return node

        def visit_ImportFrom(self, node):
            if node.module not in Evaluator.allowed_imports:
                raise EvalError("unsuported import")
            return node

        def visit_Attribute(self, node):
            if re.match("__([^_]+)__", node.attr):
                raise EvalError("unsuported __name__ attributes")
            if re.match("_([^_]+)", node.attr):
                raise EvalError("unsuported _name attributes")
            return node

        def visit_Name(self, node):
            if re.match("__([^_]+)__", node.id):
                raise EvalError("unsuported __name__ attributes")
            if re.match("_([^_]+)", node.id):
                raise EvalError("unsuported _name attributes")
            return node

        def visit_Str(self, node):
            if re.match("__([^_]+)__", node.s):
                raise EvalError("unsuported __name__ string")
            if re.match("_([^_]+)", node.s):
                raise EvalError("unsuported _name string")
            return node

    def eval(self, code, verbose=False):
        tree = ast.parse(code)

        # make source safer
        self.Transformer().visit(tree)
        tree = ast.fix_missing_locations(tree)

        if verbose:
            pprint(tree)

        co = compile(tree, filename="<ast>", mode="exec")
        exec(co, {'__builtins__': self.allowed_builtins}, {})

        return "--"


class Eval(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger(__name__)

    async def eval_coro(self, code):
        evaluator = Evaluator()

        with multiprocessing.Pool(processes=1) as pool:
            try:
                result = pool.apply_async(evaluator.eval, [code, True])
                return 0, result.get(timeout=5)

            except EvalError as e:
                return 1, str(e)

            except multiprocessing.TimeoutError:
                return 1, "Timeout: exceeded 5 seconds"

            except Exception as e:
                return 1, str(e)

    @commands.command(name='eval')
    async def _eval(self, ctx, *, body):
        """
        check if the body is executable
        check for blocked_words which could be potentionally harmful

        format embed in format
            ``` code ```
            Finished in: 00:00:00

        set color and reaction depending on success / error

        remove play reaction so the code can't be executed
        again
        """
        if not self.is_evaluatable_message(body):
            return

        blocked_words = ['delete', 'os', 'env', 'subprocess', 'open',
                         'history()', 'token']

        for x in blocked_words:
            if x.lower() in body.lower():
                embed = Embed(color=Color.red())
                embed.add_field(
                    name="Error", value=f'```\nYour code contains certain blocked words.\n```')
                embed.set_footer(icon_url=ctx.author.avatar_url)
                return await ctx.send(embed=embed)

        body = self.cleanup_code(body)
        embed = Embed(color=Color(0xffffcc))

        time_start = time.time()

        ret_code, value = await self.eval_coro(body)

        time_end = time.time()
        elapsed_time = time.strftime(
            "%H:%M:%S", time.gmtime(time_end - time_start))

        out = err = None
        if ret_code == 0:
            dots = "..." if len(value) > 1000 else ""
            embed.add_field(
                name="Output", value=f'```py\n{value[:1000]}{dots}\n```')
            embed.set_footer(
                text=f"Finished in: {elapsed_time}", icon_url=ctx.author.avatar_url)

            out = await ctx.send(embed=embed)

        else:
            embed.color = Color.red()
            embed.add_field(
                name="Error", value=f'```\n{value}\n```')
            embed.set_footer(
                text=f"Finished in: {elapsed_time}", icon_url=ctx.author.avatar_url)

            err = await ctx.send(embed=embed)

        if out:
            await ctx.message.add_reaction('\u2705')  # tick
        elif err:
            await ctx.message.add_reaction('\u2049')  # x
        else:
            await ctx.message.add_reaction('\u2705')

        await ctx.message.remove_reaction("▶", ctx.author)
        await ctx.message.remove_reaction("▶", self.bot.user)

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    def is_evaluatable_message(self, body):
        return (body.startswith("```py") and
                body.endswith("```") and
                body.count("\n") >= 2 and
                len(self.cleanup_code(body)) > 0)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.is_evaluatable_message(message.content):
            return

        if message.author.bot:
            return

        await message.add_reaction("▶")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """
        check if users clicked the play button on executable code
        the bot has to be a reactor on the executable message
        """
        message = reaction.message
        if not self.is_evaluatable_message(message.content):
            return

        if message.author.bot or user.bot or message.author != user:
            return

        if str(reaction.emoji) != "▶":
            return

        if self.bot.user not in await reaction.users().flatten():
            return

        self.log.info(f"{user} has reacted on message code message")

        ctx = commands.Context(prefix=self.bot.command_prefix, guild=message.guild,
                               channel=message.channel, message=message, author=user)
        await self._eval.callback(self, ctx, body=message.content)


def setup(bot):
    bot.add_cog(Eval(bot))
