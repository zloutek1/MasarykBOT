import discord
from discord.ext import commands
from discord import Color, Embed, Member, Object, File, PartialEmoji

import os
import inspect
import requests
from random import shuffle, choice
from types import FunctionType


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    async def emoji_list(self, ctx):
        await ctx.message.delete()

        emojis = sorted(ctx.guild.emojis, key=lambda emoji: emoji.name)
        for i in range(0, len(emojis), 10):
            await ctx.send(" ".join(list(map(str, emojis[i:i + 10]))))

        if len(emojis) == 0:
            await ctx.send("This guild has not emojis")

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    async def emoji_url(self, ctx, emoji: PartialEmoji):
        await ctx.send(emoji.url)

    @commands.command()
    async def emoji(self, ctx, emoji: PartialEmoji):
        filename = 'assets/cogs_fun_emoji.{ext}'.format(
            ext="png" if not emoji.animated else "gif")

        with open(filename, 'wb') as file:
            file.write(requests.get(emoji.url).content)
        await ctx.send(file=File(filename))

        os.remove(filename)

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command(description='For when you wanna settle the score some other way', aliases=['choice', 'pick'])
    async def choose(self, ctx, *choices):
        """Chooses between multiple choices."""
        e = Embed()

        extended_choices = list(choices) * 7
        for i in range(7):
            shuffle(extended_choices)
        chosen = choice(extended_choices)

        e.add_field(name="I choose " + chosen, value=" / ".join(choices))
        await ctx.send(embed=e)

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    async def hug(self, ctx, user: Member, intensity: int = 1):
        """Because everyone likes hugs"""

        emojis = ["(っ˘̩╭╮˘̩)っ", "(っ´▽｀)っ", "╰(*´︶`*)╯",
                  "(つ≧▽≦)つ", "(づ￣ ³￣)づ", "(づ｡◕‿‿◕｡)づ",
                  "(づ￣ ³￣)づ", "(っ˘̩╭╮˘̩)っ", "⁽₍੭ ՞̑◞ළ̫̉◟՞̑₎⁾੭",
                  "(੭ु｡╹▿╹｡)੭ु⁾⁾   ", "(*´σЗ`)σ", "(っ´▽｀)っ",
                  "(っ´∀｀)っ", "c⌒っ╹v╹ )っ", "(σ･з･)σ",
                  "(੭ु´･ω･`)੭ु⁾⁾", "(oﾟ▽ﾟ)o", "༼つ ் ▽ ் ༽つ",
                  "༼つ . •́ _ʖ •̀ . ༽つ", "╏つ ͜ಠ ‸ ͜ಠ ╏つ", "༼ つ ̥◕͙_̙◕͖ ͓༽つ",
                  "༼ つ ◕o◕ ༽つ", "༼ つ ͡ ͡° ͜ ʖ ͡ ͡° ༽つ", "(っಠ‿ಠ)っ",
                  "༼ つ ◕_◕ ༽つ", "ʕっ•ᴥ•ʔっ", "", "༼ つ ▀̿_▀̿ ༽つ",
                  "ʕ ⊃･ ◡ ･ ʔ⊃", "╏つ” ⊡ 〜 ⊡ ” ╏つ", "(⊃｡•́‿•̀｡)⊃",
                  "(っ⇀⑃↼)っ", "(.づ◡﹏◡)づ.", "(.づσ▿σ)づ.",
                  "(っ⇀`皿′↼)っ", "(.づ▣ ͜ʖ▣)づ.", "(つ ͡° ͜ʖ ͡°)つ",
                  "(⊃ • ʖ̫ • )⊃", "（っ・∀・）っ", "(つ´∀｀)つ",
                  "(っ*´∀｀*)っ", "(つ▀¯▀)つ", "(つ◉益◉)つ",
                  " ^_^ )>",
                  "───==≡≡ΣΣ((( つºل͜º)つ", "─=≡Σ((( つ◕ل͜◕)つ",
                  "─=≡Σ((( つ ◕o◕ )つ", "～～～～(/￣ｰ(･･｡)/",
                  "───==≡≡ΣΣ(づ￣ ³￣)づ", "─=≡Σʕっ•ᴥ•ʔっ",
                  "───==≡≡ΣΣ(> ^_^ )>", "─=≡Σ༼ つ ▀̿_▀̿ ༽つ",
                  "───==≡≡ΣΣ(っ´▽｀)っ", "───==≡≡ΣΣ(っ´∀｀)っ",
                  "～～(つˆДˆ)つﾉ>｡☆)ﾉ"]

        if 0 <= intensity < len(emojis):
            await ctx.send(emojis[intensity] + f" **{user}**")
        else:
            await ctx.send(choice(emojis) + f" **{user}**")

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    async def answer(self, ctx, *, question):
        e = discord.Embed()
        e.add_field(name=choice(("Yes", "No")), value=question)
        await ctx.send(embed=e)

    @commands.command()
    async def source(self, ctx, *, command: str = None):
        """Displays my full source code or for a specific command.
        To display the source code of a subcommand you can separate it by
        periods, e.g. tag.create for the create subcommand of the tag command
        or by spaces.
        """

        def extract_wrapped(decorated):
            closure = (c.cell_contents for c in decorated.__closure__)
            return next((c for c in closure if isinstance(c, FunctionType)), None)

        source_url = 'https://gitlab.com/zloutek1/MasarykBOT'
        branch = 'master'
        if command is None:
            return await ctx.send(source_url)

        if command == 'help':
            src = type(self.bot.help_command)
            module = src.__module__
            filename = inspect.getsourcefile(src)
        else:
            obj = self.bot.get_command(command.replace('.', ' '))
            if obj is None:
                return await ctx.send('Could not find command.')

            # since we found the command we're looking for, presumably anyway, let's
            # try to access the code itself
            src = extract_wrapped(obj.callback).__code__
            module = obj.callback.__module__
            filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        if not module.startswith('discord'):
            # not a built-in command
            location = os.path.relpath(filename).replace('\\', '/')
        else:
            location = module.replace('.', '/') + '.py'
            source_url = 'https://github.com/Rapptz/discord.py'
            branch = 'master'

        final_url = f'<{source_url}/blob/{branch}/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>'
        await ctx.send(final_url)

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    @commands.cooldown(rate=1, per=600, type=commands.BucketType.guild)
    async def nightsky(self, ctx):
        await ctx.send("\n".join(['.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000 ✦ \u3000\u3000\u3000\u3000\u2002\u2002 \u3000', '\u3000\u3000\u3000˚\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000*\u3000\u3000\u3000\u3000\u3000\u3000\u2008', '\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '\u3000\u3000\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000 ✦ \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000 \u3000 \u200d \u200d \u200d \u200d \u3000\u3000\u3000\u3000 \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000,\u3000\u3000\u2002\u2002\u2002\u3000', '', '.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000ﾟ\u3000\u2002\u2002\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '', '\u3000\u3000\u3000\u3000\u3000\u3000,\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u2008\u2008\u2008\u2008\u3000\u3000\u3000\u3000:alien: doot doot', '\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u2008\u2008', '\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000:sunny:\u3000\u3000\u2008\u2008\u200a\u200a\u3000\u2008\u2008\u2008\u2008\u2008\u200a\u3000\u3000\u3000\u3000\u3000\u2008\u2008\u200a\u200a\u2008\u2008\u200a\u200a\u3000\u3000\u3000\u3000*\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u2008\u2008\u200a\u200a\u3000\u2008\u2008\u2008\u3000\u3000\u3000\u3000', '\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u2008\u2008\u200a\u200a\u3000\u2008\u2008\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u2008\u2008\u200a\u200a\u3000\u2008\u2008\u2008 ✦', '\u3000\u2002\u2002\u2002\u3000\u3000\u3000,\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000*\u3000\u3000\u2008\u200a\u200a\u200a \u3000\u3000\u3000\u3000 \u3000\u3000,\u3000\u3000\u3000 \u200d \u200d \u200d \u200d \u3000 \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u2008\u3000\u3000', '\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u2008\u3000\u200a\u200a\u2008\u2008\u2008\u2008\u2008\u2008\u2008\u200a\u200a\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000˚\u3000\u3000\u3000', '\u3000 \u2002\u2002\u3000\u3000\u3000\u3000,\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u200a\u200a\u200a\u200a\u3000\u200a\u2008\u2008\u2008:rocket:\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000', '\u2008\u3000\u3000\u2002\u2002\u2002\u2002\u3000\u3000\u3000\u3000\u3000\u2008\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000*', '\u3000\u3000 \u2002\u2002\u3000\u3000\u3000\u3000\u3000 ✦ \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u200a\u200a\u200a\u200a\u200a\u200a\u3000\u2008\u2008\u2008\u2008\u2008\u2008\u2008\u2008\u3000\u3000\u3000\u3000', '\u3000\u3000\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u2008\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u2002\u2002\u2002\u2002\u3000\u3000.', '\u3000\u2008\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000 \u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u2002\u2002 \u3000', '', '\u3000˚\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000ﾟ\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '\u3000\u3000\u2008\u3000', '\u200d \u200d \u200d \u200d \u200d \u200d \u200d \u200d \u200d \u200d ,\u3000 \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000*', '.\u3000\u3000\u3000\u3000\u3000\u2008\u3000\u3000\u3000\u3000:full_moon: \u3000\u3000\u3000\u3000\u3000\u3000\u3000:earth_americas: \u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000 ✦ \u3000\u3000\u3000\u3000\u2002\u2002 \u3000', '\u3000\u3000\u3000˚\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000*\u3000\u3000\u3000\u3000\u3000\u3000\u2008', '\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '\u3000\u3000\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000 ✦ \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000 \u3000 \u200d \u200d \u200d \u200d \u3000\u3000\u3000\u3000 \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000,', '']))


def setup(bot):
    bot.add_cog(Fun(bot))
