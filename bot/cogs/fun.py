import os
from io import BytesIO
from random import choice, shuffle
from typing import Literal, Optional, Union, cast
from urllib.parse import urlparse

import requests
import unicodeit
from bot.cogs.utils.context import Context
from disnake import File, Member, PartialEmoji, User
from disnake.ext import commands
from PIL import Image

IMG_EXTS = Union[
    Literal['webp'],
    Literal['jpeg'],
    Literal['jpg'],
    Literal['png'],
    Literal['gif']
]

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def emoji_list(self, ctx: Context) -> None:
        assert ctx.guild is not None, "ERROR: command can only be invoked inside a guild"
        await ctx.message.delete()

        emojis = sorted(ctx.guild.emojis, key=lambda emoji: emoji.name)
        for i in range(0, len(emojis), 10):
            await ctx.send(" ".join(list(map(str, emojis[i:i + 10]))))

        if len(emojis) == 0:
            await ctx.send("This guild has no emojis")

    @commands.command()
    async def emoji_url(self, ctx: Context, emoji: PartialEmoji) -> None:
        await ctx.send(f"`{emoji.url}`")

    @commands.command(aliases=['emote'])
    async def emoji(self, ctx: Context, emoji: PartialEmoji) -> None:
        filename = '{name}.{ext}'.format(name = emoji.name,
                                         ext="png" if not emoji.animated else "gif")

        with open(filename, 'wb') as file:
            file.write(requests.get(emoji.url).content)
        await ctx.send(file=File(filename))

        os.remove(filename)

    @commands.command(aliases=['icon_url'])
    async def logo_url(self, ctx: Context, format: Optional[IMG_EXTS] = None) -> None:
        assert ctx.guild is not None, "ERROR: command can only be invoked inside a guild"
        if ctx.guild.icon is None:
            await ctx.send("No icon")
            return

        logo = ctx.guild.icon
        url = (logo.url if format is None else
               logo.with_format(format).url)

        await ctx.send(f"`{url}`")

    @commands.command(aliases=['icon'])
    async def logo(self, ctx: Context) -> None:
        assert ctx.guild is not None, "ERROR: command can only be invoked inside a guild"
        if ctx.guild.icon is None:
            await ctx.send("this guild has no logo")
            return

        await self.send_asset(ctx, ctx.guild.icon.url)

    @commands.command()
    async def banner_url(self, ctx: Context, format: Optional[IMG_EXTS] = None) -> None:
        assert ctx.guild is not None, "ERROR: command can only be invoked inside a guild"
        if ctx.guild.banner is None:
            await ctx.send("No banner")
            return

        banner = ctx.guild.banner
        url = (banner.url if format is None else
               banner.with_format(format).url)

        await ctx.send(f"`{url}`")

    @commands.command()
    async def banner(self, ctx: Context) -> None:
        assert ctx.guild is not None, "ERROR: command can only be invoked inside a guild"
        if ctx.guild.banner is None:
            await ctx.send("this guild has no banner")
            return

        await self.send_asset(ctx, ctx.guild.banner.url)

    @commands.command()
    async def avatar_url(self, ctx: Context, format: Optional[IMG_EXTS] = None) -> None:
        if ctx.author.avatar is None:
            await ctx.send("No avatar")
            return

        avatar = ctx.author.avatar
        url = (avatar.url if format is None else
               avatar.with_format(format).url)

        await ctx.send(f"`{url}`")

    @commands.command()
    async def avatar(self, ctx: Context, member: Optional[Union[User, Member]] = None) -> None:
        if member is None:
            member = ctx.author

        if member.avatar is None:
            await ctx.send(f"{member} has no avatar")
            return

        await self.send_asset(ctx, member.avatar.url)

    @commands.command(aliases=['choice', 'pick'])
    async def choose(self, ctx: Context, *choices: str) -> None:
        """Chooses between multiple choices."""
        if not choices:
            await ctx.send("no options to choose from")
            return

        extended_choices = list(choices) * 7
        for _ in range(7):
            shuffle(extended_choices)
        chosen = choice(extended_choices)

        await ctx.send_embed(" / ".join(choices), name="I choose " + chosen)

    @commands.command()
    async def hug(self, ctx: Context, user: Member, intensity: int = 1) -> None:
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

    @commands.command()
    async def answer(self, ctx: Context, *, question: str) -> None:
        await ctx.send_embed(question, name=choice(("Yes", "No")))

    @commands.command()
    @commands.cooldown(rate=1, per=600, type=commands.BucketType.guild)
    async def nightsky(self, ctx: Context) -> None:
        await ctx.send("\n".join(['.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000 ✦ \u3000\u3000\u3000\u3000\u2002\u2002 \u3000', '\u3000\u3000\u3000˚\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000*\u3000\u3000\u3000\u3000\u3000\u3000\u2008', '\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '\u3000\u3000\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000 ✦ \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000 \u3000 \u200d \u200d \u200d \u200d \u3000\u3000\u3000\u3000 \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000,\u3000\u3000\u2002\u2002\u2002\u3000', '', '.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000ﾟ\u3000\u2002\u2002\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '', '\u3000\u3000\u3000\u3000\u3000\u3000,\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u2008\u2008\u2008\u2008\u3000\u3000\u3000\u3000:alien: doot doot', '\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u2008\u2008', '\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000:sunny:\u3000\u3000\u2008\u2008\u200a\u200a\u3000\u2008\u2008\u2008\u2008\u2008\u200a\u3000\u3000\u3000\u3000\u3000\u2008\u2008\u200a\u200a\u2008\u2008\u200a\u200a\u3000\u3000\u3000\u3000*\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u2008\u2008\u200a\u200a\u3000\u2008\u2008\u2008\u3000\u3000\u3000\u3000', '\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u2008\u2008\u200a\u200a\u3000\u2008\u2008\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u2008\u2008\u200a\u200a\u3000\u2008\u2008\u2008 ✦', '\u3000\u2002\u2002\u2002\u3000\u3000\u3000,\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000*\u3000\u3000\u2008\u200a\u200a\u200a \u3000\u3000\u3000\u3000 \u3000\u3000,\u3000\u3000\u3000 \u200d \u200d \u200d \u200d \u3000 \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u2008\u3000\u3000', '\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u2008\u3000\u200a\u200a\u2008\u2008\u2008\u2008\u2008\u2008\u2008\u200a\u200a\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000˚\u3000\u3000\u3000', '\u3000 \u2002\u2002\u3000\u3000\u3000\u3000,\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u200a\u200a\u200a\u200a\u3000\u200a\u2008\u2008\u2008:rocket:\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000', '\u2008\u3000\u3000\u2002\u2002\u2002\u2002\u3000\u3000\u3000\u3000\u3000\u2008\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000*', '\u3000\u3000 \u2002\u2002\u3000\u3000\u3000\u3000\u3000 ✦ \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u200a\u200a\u200a\u200a\u200a\u200a\u3000\u2008\u2008\u2008\u2008\u2008\u2008\u2008\u2008\u3000\u3000\u3000\u3000', '\u3000\u3000\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u2008\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u2002\u2002\u2002\u2002\u3000\u3000.', '\u3000\u2008\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000 \u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u2002\u2002 \u3000', '', '\u3000˚\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000ﾟ\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '\u3000\u3000\u2008\u3000', '\u200d \u200d \u200d \u200d \u200d \u200d \u200d \u200d \u200d \u200d ,\u3000 \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000*', '.\u3000\u3000\u3000\u3000\u3000\u2008\u3000\u3000\u3000\u3000:full_moon: \u3000\u3000\u3000\u3000\u3000\u3000\u3000:earth_americas: \u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000 ✦ \u3000\u3000\u3000\u3000\u2002\u2002 \u3000', '\u3000\u3000\u3000˚\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000*\u3000\u3000\u3000\u3000\u3000\u3000\u2008', '\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '\u3000\u3000\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000 ✦ \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000 \u3000 \u200d \u200d \u200d \u200d \u3000\u3000\u3000\u3000 \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000,', '']))

    @commands.command()
    async def cat(self, ctx: Context, http_err_code: int) -> None:
        await self.send_asset(ctx, f"https://http.cat/{http_err_code}.jpg")

    @staticmethod
    async def send_asset(ctx: Context, url: str) -> None:
        url = str(url)
        filename = os.path.basename(urlparse(url).path)

        with open(filename, 'wb') as file:
            file.write(requests.get(url).content)
        await ctx.send(file=File(filename))

        os.remove(filename)

    @commands.command()
    async def asciify(
        self,
        ctx: Context,
        emoji: PartialEmoji,
        treshold: int = 127,
        size: int = 60,
        inverted: bool = False
    ) -> None:
        """
        Convert an emoji into an ascii version
        and send it back to the user
        """

        if size < 0 or size > 300:
            await ctx.send_error("Invalid image size")
            return

        if treshold < 0 or treshold > 255:
            await ctx.send_error("Invalid treshold")
            return

        response = requests.get(emoji.url)
        img = Image.open(BytesIO(response.content)).convert('L')
        img = img.resize((size, size))

        asciiXDots = 2
        asciiYDots = 4

        ascii = ""
        for y in range(0, img.height, asciiYDots):
            line = ""
            for x in range(0, img.width, asciiXDots):
                c = self.chunk2braille( img.crop((x, y, x+asciiXDots, y+asciiYDots)), treshold, inverted )
                line += c
            ascii += line+"\n"

        if len(ascii) > 3800:
            await ctx.send_error("output too large")
            return

        await ctx.send(ascii)

    @staticmethod
    def chunk2braille(slice: Image, treshold: int = 127, inverted: bool = False) -> str:
        """https://en.wikipedia.org/wiki/Braille_Patterns"""
        dots = [ (1 + int(inverted) + int(slice.getpixel((x, y)) < treshold)) % 2
                 for y in range(slice.height)
                 for x in range(slice.width)]

        dots = [ dots[ 0 ], dots[ 2 ],
                 dots[ 4 ], dots[ 1 ],
                 dots[ 3 ], dots[ 5 ],
                 dots[ 6 ], dots[ 7 ] ]

        return chr( 10240 + int( '0b' + ''.join(map(str, reversed(dots))), 2) )

    @commands.command()
    async def unicode(self, ctx: Context, latex: str) -> None:
        """Convert latex into unicode: https://github.com/svenkreiss/unicodeit"""
        await ctx.send(unicodeit.replace(latex.strip('`')))

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Fun(bot))
