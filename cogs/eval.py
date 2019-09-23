from discord import Embed
from discord.ext import commands
import inspect
import io
import textwrap
import traceback
from contextlib import redirect_stdout
import time


class Eval(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='eval')
    async def _eval(self, ctx, *, body):
        """Evaluates python code"""
        blocked_words = ['.delete()', 'os', 'subprocess',
                         'history()', '("token")', "('token')"]
        if ctx.author.id != self.bot.owner_id:
            for x in blocked_words:
                if x in body:
                    return await ctx.send('Your code contains certain blocked words.')
        env = {
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            'source': inspect.getsource
        }

        body = self.cleanup_code(body)
        stdout = io.StringIO()
        err = out = None
        time_start = time.time()

        embed = Embed()
        dots = "..." if len(body) > 1000 else ""
        embed.add_field(name="Input", value=body[:1000] + dots)

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        def paginate(text: str):
            '''Simple generator that paginates text.'''
            last = 0
            pages = []
            for curr in range(0, len(text)):
                if curr % 1980 == 0:
                    pages.append(text[last:curr])
                    last = curr
                    appd_index = curr
            if appd_index != len(text) - 1:
                pages.append(text[last:curr])
            return list(filter(lambda a: a != '', pages))

        # syntax check
        try:
            exec(to_compile, env)
        except Exception as e:
            err = await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')
            return await ctx.message.add_reaction('\u2049')

        # redirect output and run
        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
            time_end = time.time()
            elapsed_time = time.strftime(
                "%H:%M:%S", time.gmtime(time_end - time_start))
        except Exception:
            value = stdout.getvalue()
            err = await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            if ret is None:
                if value:
                    # print return value
                    dots = "..." if len(value) > 1000 else ""
                    embed.add_field(
                        name="Output", value=f'```py\n{value[:1000]}{dots}\n```')
                    embed.set_footer(
                        text=f"Finished in: {elapsed_time}", icon_url=ctx.author.avatar_url)
                    out = await ctx.send(embed=embed)
            else:
                self.bot._last_result = ret
                try:
                    dots = "..." if len(value) > 1000 else ""
                    embed.add_field(
                        name="Output", value=f'```py\n{value}{ret}{dots}\n```')
                    embed.set_footer(
                        text=f"Finished in: {elapsed_time}", icon_url=ctx.author.avatar_url)
                    out = await ctx.send(embed=embed)
                except Exception:
                    dots = "..." if len(value) > 1000 else ""
                    out = await ctx.send(f'```py\n{value[:1000]}{ret}{dots}\n```')

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

    @commands.Cog.listener()
    async def on_message(self, message):
        if not (message.content.startswith("```py") and message.content.endswith("```")):
            return

        if message.author.bot:
            return

        await message.add_reaction("▶")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        message = reaction.message
        if not (message.content.startswith("```py") and message.content.endswith("```")):
            return

        if message.author.bot or user.bot or message.author != user:
            return

        if str(reaction.emoji) != "▶":
            return

        if self.bot.user not in await reaction.users().flatten():
            return

        ctx = commands.Context(prefix=self.bot.command_prefix, guild=message.guild,
                               channel=message.channel, message=message, author=user)
        await self._eval.callback(self, ctx, body=message.content)


def setup(bot):
    bot.add_cog(Eval(bot))
